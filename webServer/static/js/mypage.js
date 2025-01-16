document.getElementById('logo').addEventListener('click', function () {
  window.location.href = '/';
});

document.addEventListener('DOMContentLoaded', () => {
  // 회원정보 수정 버튼 클릭 시 모달 열기
  const editProfileButton = document.getElementById('editProfileButton');
  const modal = document.getElementById('editProfileModal');
  const closeButton = document.querySelector('.close-button');
  const accountInfo = document.getElementById('account-info');

  editProfileButton.addEventListener('click', () => {
    modal.style.display = 'block';
  });

  closeButton.addEventListener('click', () => {
    modal.style.display = 'none';
  });

  window.addEventListener('click', (event) => {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });

  // 키움 API 연동 버튼 클릭
  document
    .getElementById('connectKiwoomApiButton')
    .addEventListener('click', () => {
      alert('키움 API 연동 시작!');
      fetch('/api/connect-kiwoom', { method: 'POST' })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            alert('키움 API 연동 완료!');
            document.getElementById('kiwoom-status').textContent = '연동 완료';
            accountInfo.classList.remove('blur'); // 블러 제거
          } else {
            alert('키움 API 연동 실패!');
          }
        })
        .catch((error) => console.error('키움 API 연동 중 오류 발생:', error));
    });

  // 회원정보 저장
  const updateProfileForm = document.getElementById('updateProfileForm');
  updateProfileForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const updatedData = {
      name: document.getElementById('update-name').value,
      email: document.getElementById('update-email').value,
      phone: document.getElementById('update-phone').value,
    };

    fetch('/api/update-user-info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedData),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          alert('회원정보가 성공적으로 수정되었습니다.');
          modal.style.display = 'none';
          location.reload();
        } else {
          alert('회원정보 수정 실패.');
        }
      })
      .catch((error) => console.error('회원정보 수정 중 오류 발생:', error));
  });
});

// 차트
document.addEventListener('DOMContentLoaded', () => {
  // 데이터 설정
  const labels = ['삼성전자', 'LG에너지솔루션']; // 종목명
  const investmentAmounts = [6000000, 4000000]; // 투자 금액
  const currentValues = [6500000, 3900000]; // 현재 가치

  // 상승/하락 색상 설정
  const barColors = currentValues.map((value, index) => {
    return value >= investmentAmounts[index] ? '#ff0000' : '#0000ff'; // 상승: 빨강, 하락: 파랑
  });

  // 그래프 데이터
  const investmentData = {
    labels: labels,
    datasets: [
      {
        label: '현재 가치 (원)',
        data: currentValues,
        backgroundColor: barColors, // 데이터별 색상 설정
        borderColor: barColors.map((color) => color), // 테두리 색상
        borderWidth: 1,
      },
    ],
  };

  // 그래프 옵션
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false, // 범례 비활성화
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#cfcfcf', // X축 텍스트 색상
        },
      },
      y: {
        ticks: {
          color: '#cfcfcf', // Y축 텍스트 색상
        },
        beginAtZero: true, // Y축 0부터 시작
      },
    },
  };

  // 캔버스에 그래프 렌더링
  const ctx = document.getElementById('investmentChart').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: investmentData,
    options: chartOptions,
  });
});

// 계좌정보 원형 그래프

document.addEventListener('DOMContentLoaded', () => {
  // 종목별 비중 데이터
  const data = {
    labels: ['삼성전자', 'LG에너지솔루션', '네이버', '카카오'], // 종목명
    datasets: [
      {
        label: '종목별 비중',
        data: [50, 30, 15, 5], // 비중 데이터 (%)
        backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'], // 색상
        borderColor: ['#ffffff', '#ffffff', '#ffffff', '#ffffff'], // 테두리 색상
        borderWidth: 2, // 테두리 두께
      },
    ],
  };

  // 차트 옵션
  const options = {
    responsive: true, // 반응형
    plugins: {
      legend: {
        position: 'top', // 범례 위치
        labels: {
          color: '#cfcfcf', // 텍스트 색상
          font: {
            size: 14,
          },
        },
      },
    },
  };

  // 그래프 생성
  const ctx = document.getElementById('accountPieChart').getContext('2d');
  new Chart(ctx, {
    type: 'pie', // 원형 그래프
    data: data,
    options: options,
  });
});

// 평가 손익 색상 변경
document.addEventListener('DOMContentLoaded', function () {
  const profitCells = document.querySelectorAll(
    '#holdings tbody tr td:last-child'
  );

  profitCells.forEach((cell) => {
    const profitValue = cell.textContent.replace(/[^0-9.-]/g, ''); // 숫자만 추출
    const profitNumber = parseFloat(profitValue);

    if (profitNumber > 0) {
      cell.classList.add('positive-profit');
    } else if (profitNumber < 0) {
      cell.classList.add('negative-profit');
    }
  });
});

// 로그아웃기능
document.getElementById('logoutButton').addEventListener('click', () => {
  fetch('/logout', { method: 'POST' })
    .then(() => {
      window.location.href = '/main';
    })
    .catch((error) => console.error('Error:', error));
});

// 스크롤
const profileSection = document.getElementById('profile-section');
const holdings = document.getElementById('holdings');
const investmentSection = document.getElementById('investment-section');

document.getElementById('goProfile').addEventListener('click', () => {
  profileSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
})

document.getElementById('goHoldings').addEventListener('click', () => {
  holdings.scrollIntoView({ behavior: 'smooth', block: 'center' });
})

document.getElementById('goInvestment').addEventListener('click', () => {
  investmentSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
})
