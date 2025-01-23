import pandas as pd
import numpy as np
import mysql.connector
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import multiprocessing
import warnings
import itertools
import datetime

# 경고 무시
warnings.filterwarnings("ignore")


# 데이터베이스에서 특정 종목 데이터 로드
def load_data_from_db(stock_idx):
    connection = mysql.connector.connect(
        host='project-db-cgi.smhrd.com',
        port=3307,
        database='mp_24K_DCX13_p3_2',
        user='mp_24K_DCX13_p3_2',
        password='smhrd2'
    )

    query = f"""
    SELECT stock_date, close_price, highest_price, lowest_price, trade_volume
    FROM stock_datas
    WHERE stock_idx = '{stock_idx}'
    ORDER BY stock_date ASC;
    """
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    data = pd.DataFrame(cursor.fetchall())
    connection.close()
    return data


# ARIMA 모델 학습 및 예측 함수
def train_and_predict(stock_idx):
    try:
        # 데이터 로드
        data = load_data_from_db(stock_idx)

        # 데이터 전처리
        data['stock_date'] = pd.to_datetime(data['stock_date'])
        data.set_index('stock_date', inplace=True)
        data.sort_index(inplace=True)

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

        data.fillna(method='bfill', inplace=True)

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
            except:
                continue

        # 최적의 모델로 예측
        arima_model = ARIMA(y_train, exog=exog_train, order=best_order)
        fitted_model = arima_model.fit()
        next_day_features = exog_test.iloc[-1].values.reshape(1, -1)
        next_day_forecast_log = fitted_model.forecast(steps=1, exog=next_day_features)
        next_day_forecast = np.exp(next_day_forecast_log.iloc[0])

        # 결과 계산
        current_price = np.exp(y_test.iloc[-1])
        price_change = next_day_forecast - current_price
        trend = "상승" if price_change > 0 else "하락"
        percentage_change = (price_change / current_price) * 100
        change_summary = f"{next_day_forecast} ({percentage_change:+.2f}%)"

        result = {
            "stock_idx": stock_idx,
            "current_price": current_price,
            "predicted_price": next_day_forecast,
            "trend": trend,
            "change_summary": change_summary
        }

        # 결과를 DB에 저장
        save_to_db(result)
        return result
    except Exception as e:
        print(f"[ERROR] Stock: {stock_idx}, Error: {e}")
        return None


# 결과를 데이터베이스에 저장
def save_to_db(result):
    try:
        # MySQL 연결 설정
        connection = mysql.connector.connect(
            host='project-db-cgi.smhrd.com',
            port=3307,
            database='mp_24K_DCX13_p3_2',
            user='mp_24K_DCX13_p3_2',
            password='smhrd2'
        )
        cursor = connection.cursor()

        # 기존 데이터 삭제 쿼리
        delete_query = "DELETE FROM predictions WHERE stock_idx = %s"
        cursor.execute(delete_query, (result['stock_idx'],))
        print(f"[INFO] Existing data for stock_idx {result['stock_idx']} deleted.")

        # 새로운 데이터 삽입 쿼리
        insert_query = """
        INSERT INTO prediction_results (stock_idx, change_summary, created_at)
        VALUES (%s, %s, NOW())
        """
        values = (result['stock_idx'], result['change_summary'])
        cursor.execute(insert_query, values)
        connection.commit()

        print(f"[INFO] Prediction for {result['stock_idx']} saved to DB: {result['change_summary']}")
    except mysql.connector.Error as err:
        print(f"[ERROR] Database save error: {err}")
    finally:
        # 연결 닫기
        if connection.is_connected():
            cursor.close()
            connection.close()



# 메인 함수: 병렬 처리
def main():
    stock_list = [
        "005930", "000660", "035420", "005380", "035720",
        "051910", "005490", "207940", "096770", "068270",
        "006400", "012330", "000270", "066570", "323410",
        "034020", "009830", "015760", "011200", "000120"
    ]

    # 멀티프로세싱 풀 생성
    with multiprocessing.Pool(processes=4) as pool:  # CPU 코어 수에 맞게 조정
        results = pool.map(train_and_predict, stock_list)

    # 결과 출력
    for res in results:
        if res:
            print(f"Stock: {res['stock_idx']}, Current: {res['current_price']:.2f}, "
                  f"Predicted: {res['predicted_price']:.2f}, "
                  f"Trend: {res['trend']}, Change Summary: {res['change_summary']}")


if __name__ == "__main__":
    main()
