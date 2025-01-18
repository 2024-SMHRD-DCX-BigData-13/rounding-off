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

    // 회원정보 수정
    const updateProfileForm = document.getElementById('updateProfileForm');

    updateProfileForm.addEventListener('submit', async (event) => {
        event.preventDefault();
    
        // 입력된 데이터 가져오기
        const updatedData = {
            email: document.getElementById('update-email').value.trim(), // 이메일 필드 값
            password: document.getElementById('update-password').value.trim(), // 비밀번호 필드 값
            tel: document.getElementById('update-phone').value.trim(), // 전화번호 필드 값
        };
    
        // 모든 필드 값 검증
        if (!updatedData.email || !updatedData.password || !updatedData.tel) {
            alert('모든 필드를 올바르게 입력하세요.');
            return;
        }
    
        try {
            // API 요청
            const response = await fetch('/api/update-user-info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData), // JSON 데이터로 변환
            });
    
            // HTTP 오류 처리
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '서버 응답 오류');
            }
    
            // JSON 응답 처리
            const data = await response.json();
            if (data.success) {
                alert('회원정보가 성공적으로 수정되었습니다.');
                document.getElementById('editProfileModal').style.display = 'none'; // 모달 닫기
                location.reload(); // 페이지 새로고침
            } else {
                alert(`회원정보 수정 실패: ${data.message}`);
            }
        } catch (error) {
            console.error('회원정보 수정 중 오류 발생:', error);
            alert(`오류 발생: ${error.message}`);
        }
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
const tradeSection = document.getElementById('trade-section');

document.getElementById('goProfile').addEventListener('click', () => {
  profileSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
})

document.getElementById('goHoldings').addEventListener('click', () => {
  holdings.scrollIntoView({ behavior: 'smooth', block: 'center' });
})

document.getElementById('goTrade').addEventListener('click', () => {
  tradeSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
})


// 로그인 상태 확인
document.addEventListener("DOMContentLoaded", function () {

  fetch("/api/check-login", { 
      method: "GET", 
      credentials: "include" // 세션 정보 포함
  })
  .then(response => {
      if (!response.ok) {
          // HTTP 상태 코드가 성공 범위가 아닐 경우 에러 처리
          throw new Error(`HTTP 오류: ${response.status}`);
      }
      return response.json();
  })
  .then(data => {
      // 로그인 상태를 화면에 반영
      const nameElement = document.getElementById("name");
      const emailElement = document.getElementById("email")
      const telElement = document.getElementById("tel")
      const nameField = document.getElementById("update-name");
      const emailField = document.getElementById("update-email");

      if (data.isLoggedIn) {
          nameElement.innerText = `${data.user.name}`;
          emailElement.innerText = `${data.user.email}`
          telElement.innerText = `${data.user.tel}`
          if (nameField) {
              nameField.value = data.user.name;
          }
          if (emailField) {
              emailField.value = data.user.email;
          }
      } else {
          nameElement.innerText = '로그인이 필요합니다.';
      }
  })
  .catch(error => {
      // 에러 로그 출력
      console.error("로그인 상태 확인 중 오류 발생:", error);
  });
});

// 보유 종목 데이터 출력
document.addEventListener("DOMContentLoaded", function () {
  
  fetch("/mystocks")
      .then(response => response.json())
      .then(data => {
          if (data.status === "success") {
              const stocks = data.data;
              const tableBody = document.getElementById("my-stocks-table");

              // 테이블에 데이터 추가
              stocks.forEach(stock => {
                  const row = document.createElement("tr")

                  row.innerHTML = `
                      <td>${stock["종목명"]}</td>
                      <td>${stock["현재가"]}</td>
                      <td>${stock["평가손익"]}</td>
                      <td>${stock["매입단가"]}</td>
                      <td>${stock["보유수량"]}</td>
                  `;
                  tableBody.appendChild(row);
                  const profitCells = document.querySelectorAll(
                    'tbody tr td:nth-child(3)'
                  );
                  // 평가 손익 색상 변경
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
          } else {
              console.error("데이터 로드 실패");
          }
      })
      .catch(error => console.error("Error fetching stocks data:", error));
});

// 거래 내역 출력력
document.addEventListener("DOMContentLoaded", function () {
  // /stocks API 호출
  fetch("/trade")
      .then(response => response.json())
      .then(data => {
          if (data.status === "success") {
              const trades = data.data;
              const tableBody = document.getElementById("trade-table-body");

              // 테이블에 데이터 추가
              trades.forEach(trade => {
                  const row = document.createElement("tr");
                  row.innerHTML = `
                      <td>${trade["날짜"]}</td>
                      <td>${trade["종목명"]}</td>
                      <td>${trade["평가손익"]}</td>
                      <td>${trade["거래대금"]}</td>
                      <td>${trade["거래량"]}</td>
                      <td>${trade["구분"]}</td>
                  `;
                  tableBody.appendChild(row);
                  const profitCells = document.querySelectorAll(
                    'tbody tr td:nth-child(3)'
                  );
                  // 평가 손익 색상 변경
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
          } else {
              console.error("데이터 로드 실패");
          }
      })
      .catch(error => console.error("Error fetching stocks data:", error));
});