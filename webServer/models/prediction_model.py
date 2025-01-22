from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import itertools
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

class PredictionModel:
    def __init__(self, connection):
        """
        ARIMA 모델 예측 클래스 초기화
        :param connection: MySQL 연결 객체
        """
        self.connection = connection  # MySQL 연결 객체
        self.stock_list = [  # 종목 리스트를 클래스 내부에 정의
            "005930", "000660", "035420", "005380", "035720",
            "051910", "005490", "207940", "096770", "068270",
            "006400", "012330", "000270", "066570", "323410",
            "034020", "009830", "015760", "011200", "000120"
        ]

    def load_data_from_db(self, stock_idx):
        """
        데이터베이스에서 특정 종목의 데이터를 로드
        """
        query = f"""
        SELECT stock_date, close_price, highest_price, lowest_price, trade_volume
        FROM stock_datas
        WHERE stock_idx = '{stock_idx}'
        ORDER BY stock_date ASC;
        """
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall())
        return data

    def save_prediction_to_db(self, stock_idx, change_summary):
        """
        예측 결과를 데이터베이스에 저장
        """
        query = """
        INSERT INTO prediction_results (stock_idx, change_summary)
        VALUES (%s, %s);
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (stock_idx, change_summary))
        self.connection.commit()

    def preprocess_data(self, data):
        """
        데이터 전처리 수행
        """
        data['stock_date'] = pd.to_datetime(data['stock_date'])
        data.set_index('stock_date', inplace=True)
        data.sort_index(inplace=True)

        data['close_price'] = data['close_price'].astype(float)
        data['highest_price'] = data['highest_price'].astype(float)
        data['lowest_price'] = data['lowest_price'].astype(float)
        data['trade_volume'] = data['trade_volume'].astype(float)

        data['log_close'] = np.log(data['close_price'])
        data['log_high'] = np.log(data['highest_price'])
        data['log_low'] = np.log(data['lowest_price'])
        data['log_volume'] = np.log(data['trade_volume'] + 1)

        data['ma_5'] = data['close_price'].rolling(window=5).mean()
        data['ma_20'] = data['close_price'].rolling(window=20).mean()
        data['macd'] = data['ma_5'] - data['ma_20']

        data.fillna(method='bfill', inplace=True)
        return data

    def train_and_predict(self, stock_idx):
        """
        특정 종목에 대해 ARIMA 모델 학습 및 예측 수행
        """
        try:
            data = self.load_data_from_db(stock_idx)
            if data is None or data.empty:
                print(f"[WARNING] No data for stock: {stock_idx}")
                return

            data = self.preprocess_data(data)

            train_size = int(len(data) * 0.8)
            train_data = data.iloc[:train_size]
            test_data = data.iloc[train_size:]

            y_train = train_data['log_close']
            y_test = test_data['log_close']
            exog_columns = ['log_high', 'log_low', 'log_volume', 'macd']
            exog_train = train_data[exog_columns]
            exog_test = test_data[exog_columns]

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
                except:
                    continue

            if not best_order:
                print(f"[WARNING] No suitable ARIMA order found for stock {stock_idx}")
                return

            arima_model = ARIMA(y_train, exog=exog_train, order=best_order)
            fitted_model = arima_model.fit()
            next_day_features = exog_test.iloc[-1].values.reshape(1, -1)
            next_day_forecast_log = fitted_model.forecast(steps=1, exog=next_day_features)
            next_day_forecast = np.exp(next_day_forecast_log.iloc[0])

            current_price = np.exp(y_test.iloc[-1])
            price_change = next_day_forecast - current_price
            percentage_change = (price_change / current_price) * 100

            change_summary = f"{price_change:+.2f} ({percentage_change:+.2f}%)"
            self.save_prediction_to_db(stock_idx, change_summary)

            print(f"[INFO] Stock: {stock_idx}, Change: {change_summary}")
        except Exception as e:
            print(f"[ERROR] Stock: {stock_idx}, Error: {e}")

    def train_and_predict_all(self):
        """
        모든 종목에 대해 병렬로 ARIMA 모델 학습 및 예측 수행
        """
        with ThreadPoolExecutor(max_workers=4) as executor:  # 병렬 처리 스레드 수 조정
            executor.map(self.train_and_predict, self.stock_list)
