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

// ResizeObserver 설정
const resizeObserver = new ResizeObserver(() => {
  syncHeights(); // 높이 변경 시 동기화
});

// div.custom-section 높이 변경 감지
const div = document.querySelector('div.custom-section');
resizeObserver.observe(div);


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
  yesterday.setDate(today.getDate() - 1); // 어제 날짜 계산

  const formatDate = (date) => date.toISOString().split('T')[0]; // "YYYY-MM-DD" 형식으로 변환
  return { today: formatDate(today), yesterday: formatDate(yesterday) };
}

// 오늘과 어제 데이터를 포함하도록 필터링하는 함수
function filterTodayAndYesterdayData(timestamps, prices) {
  const { today, yesterday } = getTodayAndYesterdayDates(); // 오늘과 어제 날짜 가져오기

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

    // 첫 데이터는 무조건 추가
    if (!lastTime) {
      filteredTimestamps.push(timestamp);
      filteredPrices.push(prices[index]);
      lastTime = currentTime;
      return;
    }

    // 시간 차이 계산 (단위: 분)
    const timeDiff = (currentTime - lastTime) / 1000 / 60;
    if (timeDiff >= 5) {
      filteredTimestamps.push(timestamp);
      filteredPrices.push(prices[index]);
      lastTime = currentTime; // 마지막 시간 갱신
    }
  });

  return { timestamps: filteredTimestamps, prices: filteredPrices };
}

// 차트 데이터를 업데이트하는 함수
function updateChart(newData) {
  console.log("Updating Chart with:", newData.timestamps, newData.prices);

  // 오늘과 어제 데이터를 포함하도록 필터링
  const filteredData = filterTodayAndYesterdayData(newData.timestamps, newData.prices);

  if (isFirstRequest) {
    // 처음 요청일 때 5분 단위로 필터링
    const fiveMinuteData = filterFiveMinuteData(filteredData.timestamps, filteredData.prices);
    chartData.timestamps = fiveMinuteData.timestamps;
    chartData.prices = fiveMinuteData.prices;
  } else {
    // 이후 요청에서는 새 데이터를 추가
    chartData.timestamps.push(...filteredData.timestamps);
    chartData.prices.push(...filteredData.prices);
  }

  // y축 범위 계산 (최고가 +2000, 최저가 -2000)
  const maxPrice = Math.max(...chartData.prices);
  const minPrice = Math.min(...chartData.prices);
  const yMin = Math.max(0, minPrice - 2000);
  const yMax = maxPrice + 2000;

  if (!myChart) {
    console.log("Initializing Chart...");
    myChart = new Chart(ctx, {
      type: 'line', // 차트 타입: 선 그래프
      data: {
        labels: chartData.timestamps, // x축 라벨
        datasets: [{
          data: chartData.prices, // 데이터 배열
          borderColor: 'rgb(175, 77, 77)', // 선 색상
          borderWidth: 2, // 선 두께
          pointRadius: 0 // 점 제거
        }]
      },
      options: {
        plugins: {
          legend: {
            display: false // 상단 라벨 숨기기
          }
        },
        scales: {
          x: {
            title: {
              display: true, // x축 타이틀 표시
              text: 'Time' // x축 타이틀 텍스트
            },
            ticks: {
              callback: function (value, index, values) {
                // 1시간 단위로 표시
                const timestamp = this.getLabelForValue(value);
                const date = new Date(timestamp);
                return date.getMinutes() === 0 ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
              },
              autoSkip: true // 자동 간격 조정
            }
          },
          y: {
            title: {
              display: true, // y축 타이틀 표시
              text: 'Price' // y축 타이틀 텍스트
            },
            min: yMin, // y축 최소값
            max: yMax  // y축 최대값
          }
        }
      }
    });
  } else {
    console.log("Updating Existing Chart...");
    myChart.data.labels = chartData.timestamps; // x축 라벨 업데이트
    myChart.data.datasets[0].data = chartData.prices; // y축 데이터 업데이트

    // y축 범위 동적으로 업데이트
    myChart.options.scales.y.min = yMin;
    myChart.options.scales.y.max = yMax;

    myChart.update(); // 차트 업데이트 적용
  }
}

// 서버에서 데이터를 가져오는 함수
async function fetchStockData() {
  try {
    const endpoint = isFirstRequest
      ? `/api/stocks/${stockId}/all`  // 모든 데이터를 가져오는 엔드포인트
      : `/api/stocks/${stockId}/latest`; // 최신 데이터를 가져오는 엔드포인트

    const response = await fetch(endpoint);
    const newData = await response.json();

    console.log("Fetched Data:", newData);

    // 이전 타임스탬프와 비교
    if (lastTimestamp && newData.timestamps.length > 0) {
      const latestTimestamp = newData.timestamps[newData.timestamps.length - 1];
      if (latestTimestamp === lastTimestamp) {
        console.log("[INFO] No new data received. Stopping requests.");
        clearInterval(fetchInterval); // 주기적인 요청 중단
        return;
      }
    }

    // 업데이트 및 타임스탬프 갱신
    updateChart(newData);
    if (newData.timestamps.length > 0) {
      lastTimestamp = newData.timestamps[newData.timestamps.length - 1];
    }

    isFirstRequest = false; // 첫 번째 요청 완료 플래그 설정
  } catch (error) {
    console.error('Error fetching stock data:', error);
  }
}

// 5분마다 데이터를 요청하고 차트를 업데이트합니다.
const fetchInterval = setInterval(fetchStockData, 300000);

// 페이지 로드 시 초기 데이터를 요청합니다.
fetchStockData();




// 주문 기능: 총 주문 금액 계산
function placeOrder() {
  const price = parseFloat(document.getElementById('buyPrice').value);
  const quantity = parseInt(document.getElementById('quantity').value);
  const total = price * quantity;
  document.getElementById('totalAmount').innerText =
    total.toLocaleString() + '원';
  alert('주문이 완료되었습니다!');
}

document.addEventListener("DOMContentLoaded", async () => {
  // URL 파라미터에서 'id' 값 가져오기
  const params = new URLSearchParams(window.location.search);
  const stockId = params.get('id');

  // 가격과 관련된 DOM 요소들 가져오기
  const buyPrice = document.getElementById('buyPrice');
  const quantity = document.getElementById('quantity');
  const totalAmount = document.getElementById('totalAmount');

  // 숫자 포맷팅 함수
  function formatNumberWithWon(number) {
    return new Intl.NumberFormat('ko-KR').format(number) + " 원"; // 쉼표와 "원" 추가
  }

  // 총 금액 계산 함수
  function totalPay() {
    const price = parseFloat(buyPrice.value.replace(/,/g, '') || 0); // 쉼표 제거 후 숫자로 변환
    const qty = parseFloat(quantity.value || 0); // 수량
    const total = price * qty;
    totalAmount.value = formatNumberWithWon(total); // 포맷팅 추가
  }

  // 서버에서 데이터 요청
  async function fetchStockData() {
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
        // 받아온 데이터를 DOM에 표시
        document.getElementById("stock-name").innerText = data.data.stock_name;
        document.getElementById("stock-price").innerText = data.data.current_price;
        const logoN = document.getElementById("choicelogo");
        logoN.src = stockLogo(data.data.stock_name);
        // 현재가를 buyPrice input에 설정
        if (buyPrice) {
          const currentPrice = data.data.current_price.replace(/[,원]/g, '').trim(); // "원"과 쉼표 제거
          buyPrice.value = currentPrice; // 현재가를 input 값으로 설정
          totalPay(); // 초기 총 금액 계산
        }
      } else {
        console.error("Error fetching stock data:", data.message);
        document.getElementById("stock-name").innerText = "데이터를 가져오지 못했습니다.";
      }
    } catch (error) {
      console.error("Error fetching stock data:", error);
    }
  }

  // 5초마다 데이터를 요청하여 갱신
  setInterval(fetchStockData, 5000);

  // 초기 데이터 로드
  await fetchStockData();

  // 입력 이벤트 리스너 추가
  buyPrice.addEventListener("input", totalPay);
  quantity.addEventListener("input", totalPay);
});



document.getElementById('logoutButton').addEventListener('click', () => {
  fetch('/logout', { method: 'POST' })
    .then(() => {
      window.location.href = '/main';
    })
    .catch((error) => console.error('Error:', error));
});

document.getElementById('mypageButton').addEventListener('click', () => {
  window.location.href = '/mypage'; // 마이페이지 페이지 URL
});

// 즐찾 기능 --------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const favoriteButton = document.getElementById("favoriteButton");
  const params = new URLSearchParams(window.location.search);
  const stockId = params.get("id");

  // 초기 상태 동기화
  async function syncFavoriteState() {
    if (!stockId) {
      alert("Stock ID가 URL에 없습니다.");
      return;
    }

    const email = await fetchUserEmail();
    if (!email) {
      alert("사용자 이메일을 가져오는 데 실패했습니다.");
      return;
    }

    try {
      const response = await fetch(`/api/check-favorite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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

  // 즐겨찾기 버튼 클릭 이벤트
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
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ email, stock_id: stockId }),
      });

      const data = await response.json();

      if (response.ok && data.status === "success") {
        favoriteButton.classList.toggle("active");
        alert(isActive ? "즐겨찾기에서 삭제되었습니다." : "즐겨찾기에 추가되었습니다.");
      } else {
        alert(`즐겨찾기 ${isActive ? "삭제" : "추가"} 실패: ${data.message}`);
      }
    } catch (error) {
      alert(`즐겨찾기 요청 중 오류 발생: ${error.message}`);
    }
  });

  // 사용자 이메일 가져오기
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
      } else {
        alert("로그인이 필요합니다.");
        return null;
      }
    } catch (error) {
      alert(`사용자 이메일 가져오기 중 오류 발생: ${error.message}`);
      return null;
    }
  }

  // 페이지 로드 시 즐겨찾기 상태 동기화
  syncFavoriteState();
});


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

// 로딩창 
const tdV = document.getElementById('stock-name');
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



