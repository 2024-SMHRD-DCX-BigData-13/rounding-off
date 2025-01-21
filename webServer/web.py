import mysql.connector
import time


def fetch_stocks_with_volume():
    """
    stocks 테이블에서 종목 데이터와 초기 거래량을 조회합니다.
    """
    try:
        # MySQL 연결
        connection = mysql.connector.connect(
            host="project-db-cgi.smhrd.com",
            user="mp_24K_DCX13_p3_2",
            password="smhrd2",
            database="mp_24K_DCX13_p3_2",
            port=3307
        )
        cursor = connection.cursor()

        # stocks 테이블에서 데이터 가져오기
        cursor.execute("SELECT stock_idx, stock_name FROM stocks")
        stocks = cursor.fetchall()

        result = []

        for stock in stocks:
            stock_idx = stock[0]
            stock_name = stock[1]

            # 초기 거래량 가져오기
            cursor.execute("""
                SELECT trade_volume
                FROM stock_datas
                WHERE stock_idx = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (stock_idx,))
            trade_volume_row = cursor.fetchone()
            trade_volume = trade_volume_row[0] if trade_volume_row else "데이터 없음"

            result.append({
                "stock_idx": stock_idx,
                "stock_name": stock_name,
                "trade_volume": f"{trade_volume:,}주" if trade_volume != "데이터 없음" else "데이터 없음"
            })

        return result

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error while fetching stocks and volume: {err}")
        return []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def fetch_realtime_prices(stocks):
    """
    stocks 데이터에 대해 5초마다 최신 현재가를 업데이트합니다.
    """
    try:
        # MySQL 연결
        connection = mysql.connector.connect(
            host="project-db-cgi.smhrd.com",
            user="mp_24K_DCX13_p3_2",
            password="smhrd2",
            database="mp_24K_DCX13_p3_2",
            port=3307
        )
        cursor = connection.cursor()

        while True:
            print("Fetching realtime prices...")
            for stock in stocks:
                stock_idx = stock["stock_idx"]

                # 최신 현재가 가져오기
                cursor.execute("""
                    SELECT current_price
                    FROM realtime_stocks
                    WHERE stock_idx = %s
                    ORDER BY create_at DESC
                    LIMIT 1
                """, (stock_idx,))
                current_price_row = cursor.fetchone()

                if current_price_row:
                    # 현재가 정수 변환 및 저장
                    current_price = int(float(current_price_row[0]))
                    print(f"[DEBUG] Stock: {stock_idx}, Current Price: {current_price}")
                    stock["current_price"] = f"{current_price:,}원"
                else:
                    print(f"[DEBUG] No data found for Stock: {stock_idx}")
                    stock["current_price"] = "데이터 없음"

            # 출력
            for stock in stocks:
                print({
                    "종목명": stock["stock_name"],
                    "현재가": stock.get("current_price", "데이터 없음"),
                    "거래량": stock["trade_volume"]
                })

            # 5초 대기
            time.sleep(5)

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error while fetching realtime prices: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    # 초기 데이터 가져오기
    stocks_with_volume = fetch_stocks_with_volume()

    # 5초마다 현재가 업데이트
    fetch_realtime_prices(stocks_with_volume)
