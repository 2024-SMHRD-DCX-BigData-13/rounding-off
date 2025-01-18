
document.getElementById('loginButton').addEventListener('click', () => {
  window.location.href = '/login'; // 로그인 페이지 URL
});

document.getElementById('mypageButton').addEventListener('click', () => {
  window.location.href = '/mypage'; // 마이페이지 페이지 URL
});

document.getElementById('logoutButton').addEventListener('click', () => {
  fetch('/logout', { method: 'POST' })
    .then(() => {
      window.location.href = '/main';
    })
    .catch((error) => console.error('Error:', error));
});


document.querySelector('.text-bg-primary').style.backgroundColor = '#FF69B4';

document.addEventListener('DOMContentLoaded', () => {
  // 서버에서 로그인 상태 확인
  fetch('/api/check-login')
    .then((response) => response.json())
    .then((data) => {
      if (data.isLoggedIn) {
        // 로그인 상태일 때 관심종목 섹션 표시
        document.getElementById('favorites').style.display = 'block';
        // document.getElementsByClassName('intro').style.display = 'none';
        document.getElementById('loginButton').style.display = 'none';
        document.getElementById('logoutButton').style.display = 'block';
        document.getElementById('mypageButton').style.display = 'block';
        document.getElementById('image-content').style.display = 'none';
        document.getElementById('opentext').style.display = 'none';
      }
    })
    .catch((error) => console.error('Error:', error));
});

// document.addEventListener("DOMContentLoaded", function () {
//   // /stocks API 호출
//   fetch("/stocks")
//       .then(response => response.json())
//       .then(data => {
//           if (data.status === "success") {
//               const stocks = data.data;
//               const tableBody = document.getElementById("stocks-table-body");

//               // 테이블에 데이터 추가
//               stocks.forEach(stock => {
//                   const row = document.createElement("tr");

//                   const prediction = stock["예측(다음날)"];
//                   const predictionClass = prediction.startsWith("+") ? "positive" : "negative";

//                   row.innerHTML = `
//                       <td>${stock["순위"]}</td>
//                       <td class="stockInfo" id="${stock["종목명"]}">${stock["종목명"]}</td>
//                       <td>${stock["현재가"]}</td>
//                       <td class="${predictionClass}">${stock["예측(다음날)"]}</td>
//                   `;
//                   tableBody.appendChild(row);
//               });

//               // 테이블 렌더링 후 이벤트 바인딩
//               const stockInfo = document.getElementsByClassName('stockInfo');
//               Array.from(stockInfo).forEach((element) => {
//                   element.addEventListener('click', () => {
//                       const name = element.id;
//                       const kname = encodeURIComponent(name);
//                       window.location.href = `/stockinfo?id=${kname}`;
//                   });
//               });
//           } else {
//               console.error("데이터 로드 실패");
//           }
//       })
//       .catch(error => console.error("Error fetching stocks data:", error));
// });


document.addEventListener("DOMContentLoaded", function () {
  const tableBody = document.getElementById("stocks-table-body");
  const pagination = document.getElementById("pagination");
  const navLinks = document.querySelectorAll("ul.nav.nav-underline .nav-link"); // 내비게이션 탭
  const paginationLinks = document.querySelectorAll(".pagination a"); // 페이지네이션 링크

  const recommendTab = document.getElementById("top-recommend");
  const volumeTab = document.getElementById("top-volume");
  const valueTab = document.getElementById("top-value"); // 거래대금 탭

  let allStocks = []; // 전체 데이터를 저장
  let currentPage = 1;
  const itemsPerPage = 10; // 페이지당 항목 수
  let currentSort = "prediction"; // 현재 정렬 기준 (예측 값)

  // 데이터를 가져오는 함수
  async function fetchStocksData() {
      try {
          const response = await fetch(`/stocks`);
          if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const data = await response.json();
          if (data.status === "success") {
              return data.data; // 전체 데이터 반환
          } else {
              console.error("데이터 로드 실패");
              return [];
          }
      } catch (error) {
          console.error("Error fetching stocks data:", error);
          return [];
      }
  }

  // % 값을 기준으로 데이터 정렬
  function sortStocksByPrediction(stocks) {
      return stocks.sort((a, b) => {
          const getPercentage = (text) => {
              const match = text.match(/([-+]?\d+(\.\d+)?)%/); // % 값 추출
              return match ? parseFloat(match[1]) : 0;
          };

          return getPercentage(b["예측(다음날)"]) - getPercentage(a["예측(다음날)"]);
      });
  }

  // 거래량을 기준으로 데이터 정렬
  function sortStocksByVolume(stocks) {
      return stocks.sort((a, b) => {
          const getVolume = (text) => {
              const match = text.match(/(\d+)/); // 숫자 추출
              return match ? parseInt(match[1]) : 0;
          };

          return getVolume(b["거래량"]) - getVolume(a["거래량"]);
      });
  }

  // 현재가를 기준으로 데이터 정렬 (비싼 순)
  function sortStocksByValue(stocks) {
      return stocks.sort((a, b) => {
          const getPrice = (text) => {
              const match = text.replace(/,/g, "").match(/(\d+)/); // 숫자 추출 (쉼표 제거)
              return match ? parseInt(match[1]) : 0;
          };

          return getPrice(b["현재가"]) - getPrice(a["현재가"]);
      });
  }

  // 테이블에 데이터 렌더링 (페이지 기반)
  function renderStocksTable(page) {
      tableBody.style.opacity = "0"; // 페이드 아웃 시작
      setTimeout(() => {
          tableBody.innerHTML = ""; // 기존 데이터 초기화

          const startIndex = (page - 1) * itemsPerPage;
          const endIndex = startIndex + itemsPerPage;
          const stocksToDisplay = allStocks.slice(startIndex, endIndex); // 현재 페이지 데이터 추출

          stocksToDisplay.forEach((stock, index) => {
              const row = document.createElement("tr");
              row.className = "stockInfo";
              row.dataset.current = stock["현재가"];
              row.id = stock["종목명"];

              const prediction = stock["예측(다음날)"];
              const predictionClass = prediction.startsWith("+") ? "positive" : "negative";

              // 각 셀에 스타일 추가
              row.innerHTML = `
                  <td style="text-align: center; vertical-align: middle; width: 10%;">${startIndex + index + 1}</td> <!-- 동적 순위 -->
                  <td style="text-align: center; vertical-align: middle; width: 35%;">${stock["종목명"]}</td>
                  <td style="text-align: center; vertical-align: middle; width: 15%;">${stock["현재가"]}</td>
                  <td style="text-align: center; vertical-align: middle; width: 15%;">${stock["거래량"]}</td>
                  <td style="text-align: center; vertical-align: middle; width: 25%;" class="${predictionClass}">${stock["예측(다음날)"]}</td>
              `;
              tableBody.appendChild(row);
          });

            // 주식 클릭 이벤트 추가
            const stockInfo = document.getElementsByClassName("stockInfo");
            Array.from(stockInfo).forEach((element) => {
                element.addEventListener("click", () => {
                    const name = element.id;
                    const currentPrice = element.dataset.current; // 현재가 데이터 가져오기
                    const kname = encodeURIComponent(name);
                    window.location.href = `/stockinfo?id=${kname}&currentPrice=${encodeURIComponent(currentPrice)}`;
                });
            });
          // 페이드 인 애니메이션
          tableBody.style.opacity = "1";
      }, 300); // 페이드 아웃 후 데이터 변경 (300ms 대기)
  }

  // 활성화된 탭/페이지 버튼 스타일 업데이트
  function updateActiveElement(selector, activeElement) {
      const currentActive = document.querySelector(selector);
      if (currentActive) {
          currentActive.classList.remove("active");
      }
      activeElement.classList.add("active");
  }

  // 탭별 정렬 이벤트
  recommendTab.addEventListener("click", function () {
      currentSort = "prediction"; // 정렬 기준 업데이트
      allStocks = sortStocksByPrediction(allStocks); // 데이터 정렬
      currentPage = 1; // 페이지를 1로 설정
      renderStocksTable(currentPage); // 첫 페이지 렌더링
      updateActiveElement("ul.nav.nav-underline .nav-link.active", recommendTab); // 탭 스타일 업데이트
      updateActiveElement(".pagination .active", pagination.querySelector(`[data-page="1"]`).parentElement); // 페이지 버튼 업데이트
  });

  volumeTab.addEventListener("click", function () {
      currentSort = "volume"; // 정렬 기준 업데이트
      allStocks = sortStocksByVolume(allStocks); // 데이터 정렬
      currentPage = 1; // 페이지를 1로 설정
      renderStocksTable(currentPage); // 첫 페이지 렌더링
      updateActiveElement("ul.nav.nav-underline .nav-link.active", volumeTab); // 탭 스타일 업데이트
      updateActiveElement(".pagination .active", pagination.querySelector(`[data-page="1"]`).parentElement); // 페이지 버튼 업데이트
  });

  valueTab.addEventListener("click", function () {
      currentSort = "value"; // 정렬 기준 업데이트
      allStocks = sortStocksByValue(allStocks); // 데이터 정렬
      currentPage = 1; // 페이지를 1로 설정
      renderStocksTable(currentPage); // 첫 페이지 렌더링
      updateActiveElement("ul.nav.nav-underline .nav-link.active", valueTab); // 탭 스타일 업데이트
      updateActiveElement(".pagination .active", pagination.querySelector(`[data-page="1"]`).parentElement); // 페이지 버튼 업데이트
  });

  // 페이지 버튼 클릭 이벤트
  pagination.addEventListener("click", (event) => {
      const target = event.target;
      if (target.tagName === "A" && target.dataset.page) {
          event.preventDefault(); // 기본 동작 방지
          const page = parseInt(target.dataset.page, 10);
          if (page !== currentPage) {
              currentPage = page;
              renderStocksTable(page); // 테이블 렌더링
              updateActiveElement(".pagination .active", target.parentElement); // 페이지 버튼 스타일 업데이트
          }
      }
  });

  // 초기 데이터 로드
  fetchStocksData().then(data => {
      allStocks = sortStocksByPrediction(data); // 기본 정렬: 예측 값 기준
      renderStocksTable(currentPage); // 첫 페이지 렌더링
      updateActiveElement("ul.nav.nav-underline .nav-link.active", recommendTab); // 초기 탭 활성화
      updateActiveElement(".pagination .active", pagination.querySelector(`[data-page="${currentPage}"]`).parentElement); // 초기 페이지 활성화
  });
});
