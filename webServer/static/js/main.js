
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

document.addEventListener("DOMContentLoaded", function () {
    const tableBody = document.getElementById("stocks-table-body");
    const pagination = document.getElementById("pagination");
    const recommendTab = document.getElementById("top-recommend");
    const volumeTab = document.getElementById("top-volume");
    const valueTab = document.getElementById("top-value");
  
    let allStocks = [];
    let currentPage = 1;
    const itemsPerPage = 10;
    let currentSort = "prediction";
  
    // 데이터를 가져오는 함수
    async function fetchStocksData() {
      try {
        const response = await fetch(`/stocks`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        if (data.status === "success") {
          return data.data;
        } else {
          console.error("데이터 로드 실패");
          return [];
        }
      } catch (error) {
        console.error("Error fetching stocks data:", error);
        return [];
      }
    }
  
    // 정렬 함수
    function sortStocks(stocks) {
      if (currentSort === "prediction") {
        return stocks.sort((a, b) => {
          const getPercentage = (text) => {
            const match = text.match(/([-+]?\d+(\.\d+)?)%/); // %를 포함한 값 추출
            return match ? parseFloat(match[1]) : 0; // 소수점 숫자로 변환
          };
          return getPercentage(b["예측(다음날)"]) - getPercentage(a["예측(다음날)"]);
        });
      } else if (currentSort === "volume") {
        return stocks.sort((a, b) => {
          const getVolume = (text) => {
            // 쉼표 제거 후 숫자로 변환
            const sanitizedText = text.replace(/,/g, "").trim(); // 쉼표와 공백 제거
            return parseInt(sanitizedText, 10) || 0; // 숫자로 변환
          };
          return getVolume(b["거래량"]) - getVolume(a["거래량"]);
        });
      } else if (currentSort === "value") {
        return stocks.sort((a, b) => {
          const getPrice = (text) => {
            const sanitizedText = text.replace(/,/g, "").trim(); // 쉼표와 공백 제거
            return parseInt(sanitizedText, 10) || 0; // 숫자로 변환
          };
          return getPrice(b["현재가"]) - getPrice(a["현재가"]);
        });
      }
      return stocks;
    }
  
    // 테이블 렌더링
    function renderStocksTable(page) {
      tableBody.innerHTML = ""; // 기존 데이터 초기화
    
      const startIndex = (page - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const stocksToDisplay = allStocks.slice(startIndex, endIndex);
    
      stocksToDisplay.forEach((stock, index) => {
        const row = document.createElement("tr");
        row.className = "stockInfo";
        row.dataset.current = stock["현재가"];
        row.id = stock["종목명"];
    
        // 예측값 포맷 수정
        let prediction = stock["예측(다음날)"];
        const predictionClass = prediction.includes("+") ? "positive" : "negative";
    
        // 숫자 부분과 % 부분 분리 및 소수점 제거
        prediction = prediction.replace(/([-+]?\d+)\.\d+\s*\(([-+]?\d+\.\d+%)\)/, (match, value, percent) => {
          return `${parseInt(value, 10)}원 (${percent})`;
        });
    
        row.innerHTML = `
          <td style="text-align: center; vertical-align: middle; width: 10%;">${startIndex + index + 1}</td>
          <td style="text-align: center; vertical-align: middle; width: 30%;"><div class="logoN"><img class="stocklogo" alt="Stock Logo" src="${stockLogo(stock["종목명"])}">${stock["종목명"]}</div></td>
          <td style="text-align: center; vertical-align: middle; width: 15%;">${stock["현재가"]}</td>
          <td style="text-align: center; vertical-align: middle; width: 20%;">${stock["거래량"]}</td>
          <td style="text-align: center; vertical-align: middle; width: 25%;" class="${predictionClass}">${prediction}</td>
        `;
    
        // 클릭 이벤트 추가
        row.addEventListener("click", function () {
          const id = stock["종목코드"];
          const encodedId = encodeURIComponent(id);
          window.location.href = `/stockinfo?id=${encodedId}`;
        });
    
        tableBody.appendChild(row);
      });
    }
  
    // 탭 활성화 업데이트
    function updateActiveTab(activeTab) {
      [recommendTab, volumeTab, valueTab].forEach((tab) => {
        tab.classList.remove("active");
      });
      activeTab.classList.add("active");
    }
  
    // 페이지네이션 활성화 업데이트
    function updateActivePage(activePage) {
      const pageLinks = pagination.querySelectorAll("li");
      pageLinks.forEach((link) => {
        link.classList.remove("active");
      });
      const targetPage = pagination.querySelector(`[data-page="${activePage}"]`);
      if (targetPage) {
        targetPage.parentElement.classList.add("active");
      }
    }
  
    // 데이터 갱신 함수
    async function refreshStocksData() {
      const data = await fetchStocksData();
      if (data.length > 0) {
        allStocks = sortStocks(data);
        renderStocksTable(currentPage);
      }
    }
  
    // 탭 클릭 이벤트 처리
    recommendTab.addEventListener("click", function () {
      currentSort = "prediction";
      allStocks = sortStocks(allStocks);
      currentPage = 1;
      renderStocksTable(currentPage);
      updateActiveTab(recommendTab);
      updateActivePage(1);
    });
  
    volumeTab.addEventListener("click", function () {
      currentSort = "volume";
      allStocks = sortStocks(allStocks);
      currentPage = 1;
      renderStocksTable(currentPage);
      updateActiveTab(volumeTab);
      updateActivePage(1);
    });
  
    valueTab.addEventListener("click", function () {
      currentSort = "value";
      allStocks = sortStocks(allStocks);
      currentPage = 1;
      renderStocksTable(currentPage);
      updateActiveTab(valueTab);
      updateActivePage(1);
    });
  
    // 페이지네이션 클릭 이벤트 처리
    pagination.addEventListener("click", (event) => {
      const target = event.target;
      if (target.tagName === "A" && target.dataset.page) {
        event.preventDefault();
        const page = parseInt(target.dataset.page, 10);
        if (page !== currentPage) {
          currentPage = page;
          renderStocksTable(page);
          updateActivePage(page); // 활성화 페이지 업데이트
        }
      }
    });
  
    // 초기 데이터 로드 및 5초마다 갱신
    fetchStocksData().then((data) => {
      allStocks = sortStocks(data);
      renderStocksTable(currentPage);
      updateActiveTab(recommendTab); // 기본적으로 추천 탭 활성화
      updateActivePage(1); // 초기 활성화 페이지 설정
      setInterval(refreshStocksData, 5000); // 5초마다 데이터 갱신
    });
  });
  
  document.addEventListener('DOMContentLoaded', () => {
    let isFetchingFavorites = false; // 중복 요청 방지 플래그
  
    // 서버에서 로그인 상태 확인
    fetch('/api/check-login')
      .then((response) => response.json())
      .then(async (data) => {
        if (data.isLoggedIn) {
          // 로그인 상태일 때 관심종목 섹션 표시
          document.getElementById('favorites').style.display = 'block';
          document.getElementById('loginButton').style.display = 'none';
          document.getElementById('logoutButton').style.display = 'block';
          document.getElementById('mypageButton').style.display = 'block';
          document.getElementById('image-content').style.display = 'none';
          document.getElementById('opentext').style.display = 'none';
  
          // 이메일을 기반으로 관심종목 가져오기
          const email = data.user.email;
          await fetchFavorites(email);
  
          // 5초마다 관심종목 데이터 갱신
          setInterval(() => fetchFavorites(email), 5000);
        }
      })
      .catch((error) => console.error('Error:', error));
  
    async function fetchFavorites(email) {
      // 중복 요청 방지
      if (isFetchingFavorites) return;
      isFetchingFavorites = true;
  
      const favoritesContainer = document.querySelector('#favorites .card-container');
  
      try {
        const response = await fetch('/favorites', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email }),
        });
  
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
  
        const data = await response.json();
        if (data.status === 'success') {
          renderFavorites(data.data, favoritesContainer);
        } else {
          console.error('Error fetching favorites:', data.message);
        }
      } catch (error) {
        console.error('Error fetching favorites:', error.message);
      } finally {
        isFetchingFavorites = false; // 요청 완료 후 플래그 초기화
      }
    }
  
    function renderFavorites(favorites, container) {
      container.innerHTML = ''; // 기존 데이터 초기화
  
      // 중복 제거: Set을 사용해 고유한 stock_idx만 남김
      const seen = new Set();
      const uniqueFavorites = favorites.filter((favorite) => {
        if (seen.has(favorite.stock_idx)) {
          return false; // 중복된 항목은 필터링
        }
        seen.add(favorite.stock_idx);
        return true; // 고유한 항목만 반환
      });
  
      uniqueFavorites.forEach((favorite) => {
        const card = document.createElement('div');
        card.className = 'card';
  
        // 숫자 형식 지정 (쉼표 추가)
        const formattedPrice = new Intl.NumberFormat('ko-KR').format(favorite.current_price);
  
        // 예측값 포맷 수정: 소수점을 제거하고 "원" 추가
        let formattedPrediction = favorite.prediction.replace(
          /([-+]?\d+)\.\d+\s*\(([-+]?\d+\.\d+%)\)/,
          (match, value, percent) => {
            return `${parseInt(value, 10)}원 (${percent})`;
          }
        );
  
        // 클릭 이벤트를 추가하여 stockinfo 페이지로 이동
        card.addEventListener('click', () => {
          const encodedId = encodeURIComponent(favorite.stock_idx); // ID 인코딩
          window.location.href = `stockinfo?id=${encodedId}`;
        });
  
        card.innerHTML = `
          <div class="title">
            <div class="logoN">
              <img class="stocklogo" alt="Stock Logo" src="${stockLogo(favorite.stock_name)}">
              <p>${favorite.stock_name}</p>
            </div>
          </div>
          <p class="value">${formattedPrice}원</p>
          <p class="change ${formattedPrediction.includes('+') ? 'positive' : 'negative'}">
            ${formattedPrediction}
          </p>
        `;
        container.appendChild(card);
      });
    }
  });
  

 // 로딩창 

 const tdV = document.getElementById('stocks-table-body');
 function loding () {
   if (tdV.textContent.trim() !== ""){
     const loading = document.getElementById("loading");
     const content = document.getElementById("content");
     loading.style.display = "none"; // 로딩 화면 숨김
     content.style.display = "block"; // 실제 콘텐츠 표시
     
  }
}
const observer = new MutationObserver(loding);
observer.observe(tdV, { childList: true, subtree: true, characterData: true});



 
function stockLogo (stockName){
  const logoMapping = {
    "삼성전자": "logo1.png",
    "삼성SDI": "logo1.png",
    "삼성바이오로직스": "logo1.png",
    "SK하이닉스": "logo2.png",
    "SK이노베이션": "logo2.png",
    "LG화학": "logo3.png",
    "LG전자": "logo3.png",
    "CJ대한통운": "logo4.png",
    "NAVER": "logo5.png",
    "HMM": "logo6.png",
    "POSCO홀딩스": "logo7.png",
    "기아": "logo8.png",
    "두산에너빌리티": "logo9.png",
    "셀트리온": "logo10.png",
    "카카오": "logo11.png",
    "카카오뱅크": "logo12.png",
    "한국전력": "logo13.png",
    "한화솔루션": "logo14.png",
    "현대모비스": "logo15.png",
    "현대자동차": "logo16.png"
  };
  const path = "../static/img/"
  const logoC = logoMapping[stockName] || 'red.png';
  const plus = path + logoC;
  return plus;
}