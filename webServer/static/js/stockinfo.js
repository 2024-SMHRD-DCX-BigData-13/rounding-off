document.getElementById('logo').addEventListener('click', function () {
  window.location.href = '/';
});

// 주문 기능: 총 주문 금액 계산
function placeOrder() {
  const price = parseFloat(document.getElementById('buyPrice').value);
  const quantity = parseInt(document.getElementById('quantity').value);
  const total = price * quantity;
  document.getElementById('totalAmount').innerText =
    total.toLocaleString() + '원';
  alert('주문이 완료되었습니다!');
}
const ctx = document.getElementById('stockChart').getContext('2d');

// 샘플 데이터 및 상승/하락을 반영한 데이터
const labels = ['1월', '2월', '3월', '4월', '5월'];
const dataPoints = [70000, 72000, 68000, 69000, 71000];

// 상승/하락 색상을 자동으로 적용
const barColors = dataPoints.map((value, index) => {
  if (index === 0) {
    return 'rgba(255, 99, 132, 0.8)'; // 첫 데이터는 상승으로 간주
  }
  return value > dataPoints[index - 1]
    ? 'rgba(255, 99, 132, 0.8)' // 상승: 빨강
    : 'rgba(54, 162, 235, 0.8)'; // 하락: 파랑
});

// 차트 생성
const stockChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: labels,
    datasets: [
      {
        label: '주가 변동 (막대)',
        data: dataPoints,
        backgroundColor: barColors,
        borderColor: barColors.map((color) => color.replace('0.8', '1')),
        borderWidth: 1,
      },
      {
        label: '종가 (라인)',
        data: dataPoints,
        type: 'line',
        borderColor: '#ffffff',
        borderWidth: 2,
        pointBackgroundColor: '#ffffff',
        pointRadius: 5,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: false,
        grid: {
          color: '#3a3b3d',
        },
        ticks: {
          color: '#e4e4e7',
        },
      },
      x: {
        grid: {
          color: '#3a3b3d',
        },
        ticks: {
          color: '#e4e4e7',
        },
      },
    },
    plugins: {
      legend: {
        labels: {
          color: '#e4e4e7',
        },
      },
    },
  },
});

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
