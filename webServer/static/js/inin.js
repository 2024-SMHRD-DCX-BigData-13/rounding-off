document.addEventListener("DOMContentLoaded", function () {
    const apiUrl = "http://127.0.0.1:8000/api/fetch_stock_data"; // 메인 서버 URL

    // 요청 데이터
    const requestData = {
        stock_codes: ["005930", "000660", "035420"], // 종목코드 리스트
        start_date: "20230101", // 기준일자
    };

    // 요청 보내기
    function fetchStockData() {
        fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(requestData),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                console.log("응답 데이터:", data);
                const resultDiv = document.getElementById("result");
                resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            })
            .catch((error) => {
                console.error("에러 발생:", error);
                const resultDiv = document.getElementById("result");
                resultDiv.innerHTML = `<p style="color: red;">에러 발생: ${error.message}</p>`;
            });
    }

    // 페이지 로드 시 자동 실행
    fetchStockData();
});
