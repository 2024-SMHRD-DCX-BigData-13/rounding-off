let chartStarted = false;
// 높이 동기화 함수 및 ResizeObserver
function syncHeights() {
  const form = document.querySelector('form.custom-section');
  const div = document.querySelector('div.custom-section');

  const divHeight = div.offsetHeight;
  const formHeight = form.offsetHeight;

  // 높이가 다를 때만 동기화
  if (divHeight !== formHeight) {
    form.style.height = `${divHeight}px`;
  }
}

const resizeObserver = new ResizeObserver(() => {
  syncHeights(); // 높이 변경 시 동기화
});
const div = document.querySelector('div.custom-section');
resizeObserver.observe(div);

// 로고 클릭 시 홈으로 이동
document.getElementById('logo').addEventListener('click', function () {
  window.location.href = '/';
});

// URL 파라미터에서 stockId를 가져옵니다.
const params = new URLSearchParams(window.location.search);
const stockId = params.get("id");

// 차트를 렌더링할 canvas 요소의 2D 컨텍스트를 가져옵니다.
const ctx = document.getElementById('stockChart').getContext('2d');

// Chart.js 차트 초기화 변수 및 데이터 저장소
let myChart;
let chartData = { timestamps: [], prices: [] }; // 기존 데이터를 저장
let isFirstRequest = true; // 첫 번째 요청 여부 플래그
let lastTimestamp = null; // 이전 데이터의 마지막 타임스탬프 저장

// 오늘과 어제 날짜를 "YYYY-MM-DD" 형식으로 가져오는 함수
function getTodayAndYesterdayDates() {
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const formatDate = (date) => date.toISOString().split('T')[0];
  return { today: formatDate(today), yesterday: formatDate(yesterday) };
}

// 오늘과 어제 데이터를 포함하도록 필터링하는 함수
function filterTodayAndYesterdayData(timestamps, prices) {
  const { today, yesterday } = getTodayAndYesterdayDates();
  const filteredTimestamps = [];
  const filteredPrices = [];
  timestamps.forEach((timestamp, index) => {
    if (timestamp.startsWith(today) || timestamp.startsWith(yesterday)) {
      filteredTimestamps.push(timestamp);
      filteredPrices.push(prices[index]);
    }
  });
  return { timestamps: filteredTimestamps, prices: filteredPrices };
}

// 5분 단위로 데이터를 필터링하는 함수
function filterFiveMinuteData(timestamps, prices) {
  const filteredTimestamps = [];
  const filteredPrices = [];
  let lastTime = null;
  timestamps.forEach((timestamp, index) => {
    const currentTime = new Date(timestamp);
    if (!lastTime) {
      filteredTimestamps.push(timestamp);
      filteredPrices.push(prices[index]);
      lastTime = currentTime;
      return;
    }
    const timeDiff = (currentTime - lastTime) / 1000 / 60;
    if (timeDiff >= 5) {
      filteredTimestamps.push(timestamp);
      filteredPrices.push(prices[index]);
      lastTime = currentTime;
    }
  });
  return { timestamps: filteredTimestamps, prices: filteredPrices };
}

function updateChart(newData) {
  console.log("Updating Chart with:", newData.timestamps, newData.prices);
  const filteredData = filterTodayAndYesterdayData(newData.timestamps, newData.prices);

  if (isFirstRequest) {
    const fiveMinuteData = filterFiveMinuteData(filteredData.timestamps, filteredData.prices);
    chartData.timestamps = fiveMinuteData.timestamps;
    chartData.prices = fiveMinuteData.prices;
  } else {
    chartData.timestamps.push(...filteredData.timestamps);
    chartData.prices.push(...filteredData.prices);
  }

  const maxPrice = Math.max(...chartData.prices);
  const minPrice = Math.min(...chartData.prices);
  const yMin = Math.max(0, minPrice - 2000);
  const yMax = maxPrice + 2000;

  if (!myChart) {
    console.log("Initializing Chart...");
  
    myChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: chartData.timestamps,
        datasets: [{
          data: chartData.prices,
          borderColor: 'rgb(175, 77, 77)',
          borderWidth: 2,
          pointRadius: 0
        }]
      },
      options: {
        animation: false, // 기본 애니메이션 off
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            title: { display: true, text: '시간' },
            ticks: {
              autoSkip: false,       // 자동 생략 끄기
              maxRotation: 0,        // 레이블 회전 0° (수평)
              minRotation: 0,        // 레이블 회전 0° (수평)
              callback: function(value, index, ticks) {
                const timestamp = this.getLabelForValue(value);
                const date = new Date(timestamp);
                // 24시간 형식으로 표시 (hour12: false)
                const formattedTime = date.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false
                });
                if (index === 0) {
                  return formattedTime;
                }
                const prevTimestamp = this.getLabelForValue(ticks[index - 1].value);
                const prevDate = new Date(prevTimestamp);
                if (date.getHours() !== prevDate.getHours()) {
                  return formattedTime;
                }
                return '';
              }
            }
          },
          y: {
            title: { display: true, text: '가격' },
            min: yMin,
            max: yMax
          }
        }
      }
    });
  
    // 차트 레이아웃(차트 영역)이 준비되도록 업데이트
    myChart.update();
  
    // requestAnimationFrame을 이용한 클리핑 애니메이션 (좌측부터 선이 점차 나타나는 효과)
    let startTime = null;
    const duration = 2000; // 애니메이션 시간: 2000ms
  
    function animate(timestamp) {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1); // 0 ~ 1 사이
  
      const chartArea = myChart.chartArea;
      if (!chartArea) {
        requestAnimationFrame(animate);
        return;
      }
  
      // 캔버스 클리어 후 클리핑 영역 적용하여 그리기
      myChart.clear();
      const ctxLocal = myChart.ctx;
      ctxLocal.save();
      ctxLocal.beginPath();
      ctxLocal.rect(chartArea.left, chartArea.top, chartArea.width * progress, chartArea.height);
      ctxLocal.clip();
      myChart.draw();
      ctxLocal.restore();
  
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        // 애니메이션 완료 후 최종 프레임 다시 그림 (클리핑 효과 제거)
        myChart.clear();
        myChart.draw();
      }
    }
    requestAnimationFrame(animate);
  
  } else {
    console.log("Updating Existing Chart...");
    myChart.data.labels = chartData.timestamps;
    myChart.data.datasets[0].data = chartData.prices;
    myChart.options.scales.y.min = yMin;
    myChart.options.scales.y.max = yMax;
    myChart.update();
  }
  
}

// 서버에서 데이터를 가져오는 함수 (차트 업데이트용)
async function fetchStockDataForChart() {
  try {
    const endpoint = isFirstRequest
      ? `/api/stocks/${stockId}/all`
      : `/api/stocks/${stockId}/latest`;
    const response = await fetch(endpoint);
    const newData = await response.json();
    console.log("Fetched Data:", newData);
    if (lastTimestamp && newData.timestamps.length > 0) {
      const latestTimestamp = newData.timestamps[newData.timestamps.length - 1];
      if (latestTimestamp === lastTimestamp) {
        console.log("[INFO] No new data received. Stopping requests.");
        clearInterval(fetchInterval);
        return;
      }
    }
    updateChart(newData);
    if (newData.timestamps.length > 0) {
      lastTimestamp = newData.timestamps[newData.timestamps.length - 1];
    }
    isFirstRequest = false;
  } catch (error) {
    console.error('Error fetching stock data:', error);
  }
}
// 차트 데이터 갱신 주기 (예: 300000ms = 5분)
let fetchInterval;

// 주문 기능: 총 주문 금액 계산 및 현재가 인풋은 최초 한 번만 설정
document.addEventListener("DOMContentLoaded", async () => {
  // URL 파라미터에서 'id' 값 가져오기
  const params = new URLSearchParams(window.location.search);
  const stockId = params.get('id');

  // 가격 관련 DOM 요소들
  const buyPrice = document.getElementById('buyPrice');
  const quantity = document.getElementById('quantity');
  const totalAmount = document.getElementById('totalAmount');

  // 숫자 포맷팅 함수
  function formatNumberWithWon(number) {
    return new Intl.NumberFormat('ko-KR').format(number) + " 원";
  }

  // 총 금액 계산 함수
  function totalPay() {
    const price = parseFloat(buyPrice.value.replace(/,/g, '') || 0);
    const qty = parseFloat(quantity.value || 0);
    const total = price * qty;
    totalAmount.value = formatNumberWithWon(total);
  }

  // 플래그: 현재가 인풋을 최초 한 번만 채우도록 함
  let initialPriceSet = false;

  // 서버에서 데이터를 요청하는 함수
  async function fetchStockDataForOrder() {
    if (!stockId) {
      console.error("No stock ID found in URL.");
      return;
    }
    try {
      const response = await fetch(`/stock-data?id=${encodeURIComponent(stockId)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      if (data.status === "success") {
        document.getElementById("stock-name").innerText = data.data.stock_name;
        document.getElementById("stock-price").innerText = data.data.current_price;
        const logoN = document.getElementById("choicelogo");
        logoN.src = stockLogo(data.data.stock_name);
        // 현재가를 인풋에 최초 한 번만 설정
        if (buyPrice && !initialPriceSet) {
          const currentPrice = data.data.current_price.replace(/[,원]/g, '').trim();
          buyPrice.value = currentPrice;
          totalPay();
          initialPriceSet = true;
        }
      } else {
        console.error("Error fetching stock data:", data.message);
        document.getElementById("stock-name").innerText = "데이터를 가져오지 못했습니다.";
      }
    } catch (error) {
      console.error("Error fetching stock data:", error);
    }
  }

  // 5초마다 데이터를 요청하여 갱신 (현재가는 최초 한 번만 채워짐)
  setInterval(fetchStockDataForOrder, 5000);
  await fetchStockDataForOrder();

  // 입력 이벤트 리스너 추가
  buyPrice.addEventListener("input", totalPay);
  quantity.addEventListener("input", totalPay);
});

// 로그아웃 기능
document.getElementById('logoutButton').addEventListener('click', () => {
  fetch('/logout', { method: 'POST' })
    .then(() => {
      window.location.href = '/main';
    })
    .catch((error) => console.error('Error:', error));
});

// 마이페이지 이동
document.getElementById('mypageButton').addEventListener('click', () => {
  window.location.href = '/mypage';
});

// 관심종목 기능
document.addEventListener("DOMContentLoaded", () => {
  const favoriteButton = document.getElementById("favoriteButton");
  const params = new URLSearchParams(window.location.search);
  const stockId = params.get("id");

  async function syncFavoriteState() {
    if (!stockId) {
      alert("Stock ID가 URL에 없습니다.");
      return;
    }
    const email = await fetchUserEmail();
    if (!email) {
      alert("로그인이 필요합니다!");
      window.location.href = '/login';
    } else {
      try {
        const response = await fetch(`/api/check-favorite`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ email, stock_id: stockId }),
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        if (data.status === "success") {
          if (data.isFavorite) {
            favoriteButton.classList.add("active");
          } else {
            favoriteButton.classList.remove("active");
          }
        } else {
          alert(`상태 동기화 실패: ${data.message}`);
        }
      } catch (error) {
        alert(`상태 동기화 중 오류 발생: ${error.message}`);
      }
    }
  }
  favoriteButton.addEventListener("click", async () => {
    if (!stockId) {
      alert("Stock ID가 URL에 없습니다.");
      return;
    }
    const isActive = favoriteButton.classList.contains("active");
    const endpoint = isActive ? "/fav_delete" : "/fav_insert";
    const email = await fetchUserEmail();
    if (!email) {
      alert("사용자 이메일을 가져오는 데 실패했습니다.");
      return;
    }
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, stock_id: stockId }),
      });
      const data = await response.json();
      if (response.ok && data.status === "success") {
        favoriteButton.classList.toggle("active");
        alert(isActive ? "관심종목에서 삭제되었습니다." : "관심종목에 추가되었습니다.");
      } else {
        alert(`관심종목 ${isActive ? "삭제" : "추가"} 실패: ${data.message}`);
      }
    } catch (error) {
      alert(`관심종목 요청 중 오류 발생: ${error.message}`);
    }
  });

  async function fetchUserEmail() {
    try {
      const response = await fetch("/api/check-login", {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      if (data.isLoggedIn) {
        return data.user.email;
      }
    } catch (error) {
      console.error(error);
    }
  }

  syncFavoriteState();
});

// 로고 매핑 (중복 정의 방지를 위해 아래 함수는 위쪽과 동일한 함수로 사용)
function stockLogo(stockName) {
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
  const path = "../static/img/";
  return path + (logoMapping[stockName] || "red.png");
}

// 로딩창 처리
const tdV = document.getElementById('stock-name');
function loding() {
  if (tdV.textContent.trim() !== "") {
    const loading = document.getElementById("loading");
    const content = document.getElementById("content");
    loading.style.display = "none";
    content.style.display = "block";

    // 로딩이 완료된 후 차트 작업을 시작 (한 번만 실행)
    if (!chartStarted) {
      fetchStockDataForChart(); // 최초 데이터 요청
      fetchInterval = setInterval(fetchStockDataForChart, 300000);
      chartStarted = true;
    }
  }
}
const observer = new MutationObserver(loding);
observer.observe(tdV, { childList: true, subtree: true, characterData: true });

// 매매 기능
async function placeOrder() {
  const params = new URLSearchParams(window.location.search);
  const stockId = params.get("id");
  const tradeType = document.getElementById('orderType').value;
  const price = parseFloat(document.getElementById("buyPrice").value);
  const quantity = parseInt(document.getElementById("quantity").value);
  console.log(stockId, price, quantity, tradeType);

  if (!stockId || isNaN(price) || isNaN(quantity)) {
    alert("필수 정보가 누락되었습니다!");
    return;
  }

  try {
    const response = await fetch("/trade/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        stock_id: stockId,
        quantity: quantity,
        price: price,
        trade_type: tradeType,
      }),
    });
    const result = await response.json();
    if (response.ok) {
      alert(`주문 상태: ${result.status}\n메시지: ${result.message}`);
    } else {
      alert(`주문 실패: ${result.detail}`);
    }
  } catch (error) {
    console.error("주문 요청 중 오류 발생:", error);
    alert("주문 요청 중 오류가 발생했습니다.");
  }
}
