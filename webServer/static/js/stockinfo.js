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

const params = new URLSearchParams(window.location.search);
const stockId = params.get('id');
const stockPrice = params.get('currentPrice');

if (stockId) {
  const stockNameElement = document.getElementById('stock-name');

  if (stockNameElement) {
    stockNameElement.textContent = `${stockId}`;
  }
}
// `stock-price` 요소에 현재가 표시
if (stockPrice) {
  const stockPriceElement = document.getElementById('stock-price');
  const buyPriceElement = document.getElementById('buyPrice');
  if (stockPriceElement) {
    const formattedPrice = stockPrice.replace(/[^0-9]/g, '').replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '원'; // 숫자 포맷 후 '원' 추가
    stockPriceElement.textContent = formattedPrice;
  }
  if (buyPriceElement) {
    const numericPrice = stockPrice.replace(/[^0-9]/g, ''); // 숫자만 추출
    buyPriceElement.value = numericPrice; // `value` 속성에 설정
  }
}


const buyPrice = document.getElementById('buyPrice');
const quantity = document.getElementById('quantity');
const totalAmount = document.getElementById('totalAmount');


function formatNumber(number){
  return new Intl.NumberFormat('ko-KR').format(number);
}

function totalPay() {
  const price = parseFloat(buyPrice.value || 0);
  const qty = parseFloat(quantity.value || 0);
  const total = price*qty;
  totalAmount.value = formatNumber(total);
}

buyPrice.addEventListener("input", totalPay);
quantity.addEventListener("input", totalPay);

window.addEventListener("DOMContentLoaded", function(){
const total = parseFloat(buyPrice.value || 0)*parseFloat(quantity.value || 0);
totalAmount.value = formatNumber(total);
})