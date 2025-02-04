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
            return match ? parseFloat(match[1]) : 0;
          };
          return getPercentage(b["예측(다음날)"]) - getPercentage(a["예측(다음날)"]);
        });
      } else if (currentSort === "volume") {
        return stocks.sort((a, b) => {
          const getVolume = (text) => {
            const sanitizedText = text.replace(/,/g, "").trim();
            return parseInt(sanitizedText, 10) || 0;
          };
          return getVolume(b["거래량"]) - getVolume(a["거래량"]);
        });
      } else if (currentSort === "value") {
        return stocks.sort((a, b) => {
          const getPrice = (text) => {
            const sanitizedText = text.replace(/,/g, "").trim();
            return parseInt(sanitizedText, 10) || 0;
          };
          return getPrice(b["현재가"]) - getPrice(a["현재가"]);
        });
      }
      return stocks;
    }
  
    // 테이블 렌더링
    function renderStocksTable(page) {
      tableBody.innerHTML = "";
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
        // 숫자 부분 추출 (예: "+0.00 (0.00%)" -> 0)
        let rawMatch = prediction.match(/([-+]?\d+(\.\d+)?)/);
        let predictionNumber = rawMatch ? parseFloat(rawMatch[0]) : 0;
        let predictionClass = "";
        let formattedPrediction = "";
        if (Math.abs(predictionNumber) < 1e-6) {
          predictionClass = "neutral";
          formattedPrediction = "0원 (0.00%)";
        } else if (predictionNumber > 0) {
          predictionClass = "positive";
          formattedPrediction = prediction.replace(/([-+]?\d+)\.\d+\s*\(([-+]?\d+\.\d+%)\)/, (match, value, percent) => {
            return `${parseInt(value, 10)}원 (${percent})`;
          });
        } else {
          predictionClass = "negative";
          formattedPrediction = prediction.replace(/([-+]?\d+)\.\d+\s*\(([-+]?\d+\.\d+%)\)/, (match, value, percent) => {
            return `${parseInt(value, 10)}원 (${percent})`;
          });
        }
    
        row.innerHTML = `
          <td style="text-align: center; vertical-align: middle; width: 10%;">${startIndex + index + 1}</td>
          <td style="text-align: center; vertical-align: middle; width: 30%;">
            <div class="logoN">
              <img class="stocklogo" alt="Stock Logo" src="${stockLogo(stock["종목명"])}">${stock["종목명"]}
            </div>
          </td>
          <td style="text-align: center; vertical-align: middle; width: 15%;">${stock["현재가"]}</td>
          <td style="text-align: center; vertical-align: middle; width: 20%;">${stock["거래량"]}</td>
          <td style="text-align: center; vertical-align: middle; width: 25%;" class="${predictionClass}">${formattedPrediction}</td>
        `;
    
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
  
    pagination.addEventListener("click", (event) => {
      const target = event.target;
      if (target.tagName === "A" && target.dataset.page) {
        event.preventDefault();
        const page = parseInt(target.dataset.page, 10);
        if (page !== currentPage) {
          currentPage = page;
          renderStocksTable(page);
          updateActivePage(page);
        }
      }
    });
  
    fetchStocksData().then((data) => {
      allStocks = sortStocks(data);
      renderStocksTable(currentPage);
      updateActiveTab(recommendTab);
      updateActivePage(1);
      setInterval(refreshStocksData, 5000);
    });
  });
  
  document.addEventListener('DOMContentLoaded', () => {
    let isFetchingFavorites = false;
  
    fetch('/api/check-login')
      .then((response) => response.json())
      .then(async (data) => {
        if (data.isLoggedIn) {
          document.getElementById('favorites').style.display = 'block';
          document.getElementById('loginButton').style.display = 'none';
          document.getElementById('logoutButton').style.display = 'block';
          document.getElementById('mypageButton').style.display = 'block';
          document.getElementById('image-content').style.display = 'none';
          document.getElementById('opentext').style.display = 'none';
  
          const email = data.user.email;
          await fetchFavorites(email);
          setInterval(() => fetchFavorites(email), 5000);
        }
      })
      .catch((error) => console.error('Error:', error));
  
    async function fetchFavorites(email) {
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
        isFetchingFavorites = false;
      }
    }
  
    function renderFavorites(favorites, container) {
      container.innerHTML = '';
  
      const seen = new Set();
      const uniqueFavorites = favorites.filter((favorite) => {
        if (seen.has(favorite.stock_idx)) {
          return false;
        }
        seen.add(favorite.stock_idx);
        return true;
      });
  
      uniqueFavorites.forEach((favorite) => {
        const card = document.createElement('div');
        card.className = 'card';
  
        const formattedPrice = new Intl.NumberFormat('ko-KR').format(favorite.current_price);
  
        // 예측값 처리
        let rawPredictionMatch = favorite.prediction.match(/([-+]?\d+(\.\d+)?)/);
        let predictionNumber = rawPredictionMatch ? parseFloat(rawPredictionMatch[0]) : 0;
        let predictionClass = "";
        let formattedPrediction = "";
        if (Math.abs(predictionNumber) < 1e-6) {
          predictionClass = "neutral";
          formattedPrediction = "0원 (0.00%)";
        } else if (predictionNumber > 0) {
          predictionClass = "positive";
          formattedPrediction = favorite.prediction.replace(
            /([-+]?\d+)\.\d+\s*\(([-+]?\d+\.\d+%)\)/,
            (match, value, percent) => {
              return `${parseInt(value, 10)}원 (${percent})`;
            }
          );
        } else {
          predictionClass = "negative";
          formattedPrediction = favorite.prediction.replace(
            /([-+]?\d+)\.\d+\s*\(([-+]?\d+\.\d+%)\)/,
            (match, value, percent) => {
              return `${parseInt(value, 10)}원 (${percent})`;
            }
          );
        }
  
        card.addEventListener('click', () => {
          const encodedId = encodeURIComponent(favorite.stock_idx);
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
          <p class="change ${predictionClass}">
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
     loading.style.display = "none";
     content.style.display = "block";
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
  return path + logoC;
}
