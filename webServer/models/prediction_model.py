import pandas as pd  # 데이터프레임 처리 라이브러리
import numpy as np  # 수학 연산 라이브러리
import itertools  # 파라미터 조합 생성용 라이브러리
from statsmodels.tsa.arima.model import ARIMA  # ARIMA 모델
import mysql.connector  # MySQL 연결 라이브러리
import warnings  # 경고 무시용 라이브러리

# 경고 무시
warnings.filterwarnings("ignore")


class PredictionModel:
    def __init__(self, connection):
        """
        ARIMA 모델 예측 클래스 초기화
        :param connection: MySQL 연결 객체
        """
        self.connection = connection  # MySQL 연결 객체

    def load_data_from_db(self, stock_idx):
        """
        데이터베이스에서 특정 종목의 데이터를 로드
        :param stock_idx: 종목 코드
        :return: 로드된 데이터 (DataFrame)
        """
        try:
            query = f"""
            SELECT stock_date, close_price, highest_price, lowest_price, trade_volume
            FROM stock_datas
            WHERE stock_idx = '{stock_idx}'
            ORDER BY stock_date ASC;
            """
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            data = pd.DataFrame(cursor.fetchall())

            if data.empty:
                raise ValueError(f"No data found for stock {stock_idx}")

            return data
        except Exception as e:
            print(f"[ERROR] Failed to load data for stock {stock_idx}: {e}")
            return None

    def save_prediction_to_db(self, stock_idx, change_summary):
        """
        예측 결과를 데이터베이스에 저장
        :param stock_idx: 종목 코드
        :param change_summary: 예측 결과 요약
        """
        try:
            query = """
            INSERT INTO prediction_results (stock_idx, change_summary)
            VALUES (%s, %s);
            """
            cursor = self.connection.cursor()
            cursor.execute(query, (stock_idx, change_summary))
            self.connection.commit()
        except Exception as e:
            print(f"[ERROR] Failed to save prediction for stock {stock_idx}: {e}")

    def preprocess_data(self, data):
        """
        데이터 전처리 수행
        :param data: 원본 데이터 (DataFrame)
        :return: 전처리된 데이터
        """
        data['stock_date'] = pd.to_datetime(data['stock_date'])
        data.set_index('stock_date', inplace=True)
        data.sort_index(inplace=True)

        # 값 변환
        data['close_price'] = data['close_price'].astype(float)
        data['highest_price'] = data['highest_price'].astype(float)
        data['lowest_price'] = data['lowest_price'].astype(float)
        data['trade_volume'] = data['trade_volume'].astype(float)

        # 로그 변환
        data['log_close'] = np.log(data['close_price'])
        data['log_high'] = np.log(data['highest_price'])
        data['log_low'] = np.log(data['lowest_price'])
        data['log_volume'] = np.log(data['trade_volume'] + 1)

        # 이동 평균 및 기술적 지표 추가
        data['ma_5'] = data['close_price'].rolling(window=5).mean()
        data['ma_20'] = data['close_price'].rolling(window=20).mean()
        data['macd'] = data['ma_5'] - data['ma_20']

        # 결측값 처리
        data.fillna(method='bfill', inplace=True)

        return data

    def train_and_predict(self, stock_idx):
        """
        ARIMA 모델을 학습하고 예측 수행
        :param stock_idx: 종목 코드
        """
        try:
            # 데이터 로드
            data = self.load_data_from_db(stock_idx)
            if data is None:
                return

            # 데이터 전처리
            data = self.preprocess_data(data)

            # 훈련 및 테스트 데이터 분리
            train_size = int(len(data) * 0.8)
            train_data = data.iloc[:train_size]
            test_data = data.iloc[train_size:]

            y_train = train_data['log_close']
            y_test = test_data['log_close']
            exog_columns = ['log_high', 'log_low', 'log_volume', 'macd']
            exog_train = train_data[exog_columns]
            exog_test = test_data[exog_columns]

            # ARIMA 모델 최적화 (Grid Search)
            p = d = q = range(0, 3)
            pdq = list(itertools.product(p, d, q))
            best_aic = float("inf")
            best_order = None

            for order in pdq:
                try:
                    model = ARIMA(y_train, exog=exog_train, order=order)
                    result = model.fit()
                    if result.aic < best_aic:
                        best_aic = result.aic
                        best_order = order
                except Exception:
                    continue

            if not best_order:
                print(f"[WARNING] No suitable ARIMA order found for stock {stock_idx}.")
                return

            # 최적의 모델로 예측
            arima_model = ARIMA(y_train, exog=exog_train, order=best_order)
            fitted_model = arima_model.fit()
            next_day_features = exog_test.iloc[-1].values.reshape(1, -1)
            next_day_forecast_log = fitted_model.forecast(steps=1, exog=next_day_features)
            next_day_forecast = np.exp(next_day_forecast_log.iloc[0])

            # 결과 계산
            current_price = np.exp(y_test.iloc[-1])
            price_change = next_day_forecast - current_price
            percentage_change = (price_change / current_price) * 100

            # 변화 요약 생성
            change_summary = f"{price_change:+.2f} ({percentage_change:+.2f}%)"

            # 데이터 저장
            self.save_prediction_to_db(stock_idx, change_summary)

        except Exception as e:
            print(f"[ERROR] Stock: {stock_idx}, Error: {e}")
