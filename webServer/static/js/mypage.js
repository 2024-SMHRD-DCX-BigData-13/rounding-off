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
  const path = "../static/img/"
  const logoC = logoMapping[stockName] || 'red.png';
  const plus = path + logoC;
  return plus;
}

document.getElementById('logo').addEventListener('click', function () {
  window.location.href = '/';
});




// const interest = document.getElementById('interest');
// const interestModal= document.getElementById('interestModal');

// interest.addEventListener('click',() => {
//   interestModal.style.display = 'block';
// });

// window.addEventListener('click', (event) => {
//   if(event.target === interestModal){
//     interestModal.style.display = 'none';
//   }
// });





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

    // 회원 정보 수정
    const updateProfileForm = document.getElementById('updateProfileForm');
    const passwordInput = document.getElementById('update-password');
    const passwordCheckInput = document.getElementById('password-check');
    const telInput = document.getElementById('update-phone');

    // 세션에서 현재 비밀번호와 전화번호 가져오기
    const sessionPassword = document.body.dataset.sessionPassword;
    const sessionTel = document.body.dataset.sessionTel;
    

    updateProfileForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const updatedData = {
            email: document.getElementById('update-email').value.trim(),
            password: passwordInput.value.trim(),
            tel: telInput.value.trim(),
        };

        // 모든 필드 값 검증
        if (!updatedData.email || !updatedData.password || !updatedData.tel) {
            alert('모든 필드를 올바르게 입력하세요.');
            return;
        }

        // 비밀번호 확인
        const password = passwordInput.value.trim();
        const passwordCheck = passwordCheckInput.value.trim();
        if (password !== passwordCheck) {
            alert('비밀번호가 일치하지 않습니다. 다시 확인해주세요.');
            passwordInput.focus();
            return;
        }

        // 기존 비밀번호와 비교
        if (sessionPassword && password === sessionPassword) {
            alert('기존 비밀번호와 동일합니다. 다른 비밀번호를 입력해주세요.');
            passwordInput.focus();
            return;
        }

        // 기존 전화번호와 비교
        // if (sessionTel && updatedData.tel === sessionTel) {
        //     alert('기존 전화번호와 동일합니다. 다른 전화번호를 입력해주세요.');
        //     telInput.focus();
        //     return;
        // }

        try {
            const response = await fetch('/api/update-user-info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '알 수 없는 오류가 발생했습니다.');
            }

            const data = await response.json();
            if (data.success) {
                alert('회원정보가 성공적으로 수정되었습니다.');
                document.getElementById('editProfileModal').style.display = 'none';
                location.reload();
            } else {
                alert(`회원정보 수정 실패: ${data.message}`);
            }
        } catch (error) {
            console.error('회원정보 수정 중 오류 발생:', error);
            alert(`오류 발생: ${error.message}`);
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
const tradeSection = document.getElementById('trade-section');
const notbuy = document.getElementById('notbuy');

document.getElementById('goProfile').addEventListener('click', () => {
  profileSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
})
document.getElementById('goNotBuy').addEventListener('click', () => {
  notbuy.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
      const telField = document.getElementById("update-phone");

      if (data.isLoggedIn) {
          nameElement.innerText = `${data.user.name}`;
          emailElement.innerText = `${data.user.email}`
          telElement.innerText = `${data.user.tel}`
          if (nameField) {
              nameField.value = data.user.name;
          }
          if (emailField) {
              emailField.value = data.user.email;
          }if (telField) {
            telField.value = data.user.tel;
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

document.addEventListener("DOMContentLoaded", function () {
  fetchHoldings();
  fetchAccountInfo();
});

// 🔹 계좌 정보 및 미체결 내역 요청
async function fetchAccountInfo() {
  try {
    const response = await fetch("/account/info");
    const data = await response.json();

    if (data.status === "success") {
      updateAccountUI(data.account_info);
      updatePendingOrdersUI(data.pending_orders);
    } else {
      console.error("계좌 정보 로드 실패:", data.detail);
    }
  } catch (error) {
    console.error("계좌 정보 요청 오류:", error);
  }
}

// 🔹 실시간 미체결 내역 요청 (5초마다 실행)
async function fetchPendingOrders() {
  try {
    const response = await fetch("/account/pending-orders");
    const data = await response.json();

    if (data.status === "success") {
      updatePendingOrdersUI(data.data);
    } else {
      console.error("실시간 미체결 데이터 로드 실패:", data.detail);
    }
  } catch (error) {
    console.error("실시간 미체결 데이터 요청 오류:", error);
  }
}

// 🔹 계좌 정보 UI 업데이트
function updateAccountUI(account) {
  if (!account) {
    console.warn("[WARNING] 계좌 정보 데이터가 없음.");
    return;
  }

  const accountNumberElem = document.getElementById("account-number");
  const balanceElem = document.getElementById("balance");
  const profitRateElem = document.getElementById("total-profit-rate");

  if (!accountNumberElem || !balanceElem || !profitRateElem) {
    console.error("[ERROR] 계좌 정보 UI 요소를 찾을 수 없음.");
    return;
  }

  accountNumberElem.textContent = account.account_number || "-";
  balanceElem.textContent = account.balance ? account.balance.toLocaleString() + "원" : "-";
  profitRateElem.textContent = account.total_profit_rate ? account.total_profit_rate + "%" : "-";
}

// 🔹 미체결 내역 UI 업데이트
function updatePendingOrdersUI(orders) {
  const tableBody = document.getElementById("notbuy-tbody");
  const loadMoreBtn = document.getElementById("pending-load-more-btn"); // 더보기 버튼
  if (!tableBody || !loadMoreBtn) {
    console.error("[ERROR] 미체결 내역 테이블 또는 더보기 버튼을 찾을 수 없음.");
    return;
  }

  tableBody.innerHTML = ""; // 기존 내용 초기화

  // 🔹 주문가 없는 데이터, 체결된 데이터 제외
  const filteredOrders = (Array.isArray(orders) ? orders : []).filter(order => order);

  if (filteredOrders.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;">미체결 내역 없음</td></tr>`;
    loadMoreBtn.style.display = "none"; // 데이터 없으면 버튼 숨김
    return;
  }

  const maxVisible = 5; // 기본으로 표시할 개수
  let showingAll = false; // 전체 보기 상태

  function renderTable(limit) {
    tableBody.innerHTML = ""; // 테이블 초기화
    filteredOrders.slice(0, limit).forEach(order => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><img class="choicelogo" src="${stockLogo(order.stock_name)}">${order.stock_name || "-"}</td>
        <td>${order.price ? order.price.toLocaleString() + "원" : "-"}</td>
        <td>${order.quantity ? order.quantity.toLocaleString() + "주" : "-"}</td>
        <td>${order.status || "-"}</td>
        <button class="btn btn-primary cancel-order-btn" value="${order.order_number}">취소</button>
      `;
      tableBody.appendChild(row);
    });

    // 🔹 '더보기' 버튼 처리
    if (filteredOrders.length > maxVisible) {
      loadMoreBtn.style.display = "block"; // 버튼 표시
      loadMoreBtn.textContent = showingAll ? "숨기기" : "더보기";
    } else {
      loadMoreBtn.style.display = "none"; // 데이터가 적으면 버튼 숨김
    }
  }

  // 🔹 초기 5개만 표시
  renderTable(maxVisible);

  // 🔹 '더보기' 버튼 클릭 이벤트
  loadMoreBtn.onclick = function () {
    showingAll = !showingAll;
    renderTable(showingAll ? filteredOrders.length : maxVisible);
  };
}

// 🔹 보유 종목 데이터 가져와 테이블 & 원형 차트 업데이트
async function fetchHoldings() {
  try {
    const response = await fetch("/account/holdings");
    const data = await response.json();

    if (data.status === "success") {
      const stocks = data.data;
      updateHoldingsTable(stocks);
      updateHoldingsChart(stocks);
    } else {
      console.error("보유 종목 데이터 로드 실패:", data.detail);
    }
  } catch (error) {
    console.error("보유 종목 데이터 요청 오류:", error);
  }
}

// 🔹 보유 종목 테이블 업데이트
function updateHoldingsTable(stocks) {
  const tableBody = document.getElementById("my-stocks-table");
  tableBody.innerHTML = "";

  let totalProfit = 0;
  let totalInvestment = 0;

  stocks.forEach(stock => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><div class="logomm"><img class="choicelogo" src="${stockLogo(stock.stock_name)}">${stock.stock_name}</div></td>
      <td>${stock.current_price.toLocaleString()}원</td>
      <td>${stock.evaluation_profit.toLocaleString()}원</td>
      <td>${stock.buy_price.toLocaleString()}원</td>
      <td>${stock.quantity}주</td>
    `;
    tableBody.appendChild(row);

    totalProfit += stock.evaluation_profit;
    totalInvestment += stock.buy_price * stock.quantity;
  });

  let totalProfitRate = totalInvestment > 0 ? (totalProfit / totalInvestment) * 100 : null;

  fetchAccountInfo(totalProfitRate);

  const profitCells = document.querySelectorAll("tbody tr td:nth-child(3)");
  profitCells.forEach((cell) => {
    const profitValue = cell.textContent.replace(/[^0-9.-]/g, "");
    const profitNumber = parseFloat(profitValue);

    if (profitNumber > 0) {
      cell.classList.add("positive-profit");
    } else if (profitNumber < 0) {
      cell.classList.add("negative-profit");
    }
  });
}

// 🔹 계좌 정보 및 미체결 내역 요청
async function fetchAccountInfo(totalProfitRate = null) {
  try {
    console.log("[DEBUG] Fetching account info from main server...");
    const response = await fetch("/account/info");
    const data = await response.json();

    console.log("[INFO] Account & Pending Orders received:", data);

    if (data.status === "success") {
      updateAccountUI(data.account_info, totalProfitRate);
      updatePendingOrdersUI(data.pending_orders);
    } else {
      console.error("계좌 정보 로드 실패:", data.detail);
    }
  } catch (error) {
    console.error("계좌 정보 요청 오류:", error);
  }
}


// 🔹 보유 종목 비중 차트 업데이트
function updateHoldingsChart(stocks) {
  const labels = stocks.map(stock => stock.stock_name);
  const values = stocks.map(stock => stock.current_price * stock.quantity);

  // 🔹 자동 색상 생성 (종목 개수에 맞게)
  const backgroundColors = generateRandomColors(stocks.length);

  const ctx = document.getElementById("accountPieChart").getContext("2d");

  // 기존 차트가 있다면 삭제 후 새로 생성
  if (window.myPieChart) {
    window.myPieChart.destroy();
  }

  window.myPieChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          label: "종목별 비중",
          data: values,
          backgroundColor: backgroundColors,
          borderColor: "#ffffff",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#cfcfcf",
            font: { size: 14 },
          },
        },
      },
    },
  });
}

// 🔹 랜덤 색상 생성 함수 (종목 개수에 맞게)
function generateRandomColors(count) {
  const colors = [];
  for (let i = 0; i < count; i++) {
    const randomColor = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
    colors.push(randomColor);
  }
  return colors;
}

// 거래 내역 데이터 출력
document.addEventListener("DOMContentLoaded", function () {
  fetch("/account/trade-history")
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        const trades = data.data;
        updateTradeHistoryUI(trades);
      } else {
        console.error("거래 내역 데이터 로드 실패:", data.detail);
      }
    })
    .catch(error => console.error("거래 내역 데이터 요청 오류:", error));
});

// 거래 내역 UI 업데이트
function updateTradeHistoryUI(trades) {
  const tableBody = document.getElementById("trade-table-body");
  const hisLoadMoreBtn = document.getElementById("his-load-more-btn");
  tableBody.innerHTML = ""; // 기존 내용 제거

  const maxVisible = 5;  // 기본으로 표시할 개수
  const maxLimit = 20;  // 최대 표시 개수
  let showingAll = false; // 모든 데이터가 보이는지 여부

  // 🔹 데이터 역순 정렬 (최신 거래 내역이 위로)
  trades.reverse();

  // 🔹 최대 20개까지만 사용
  const limitedTrades = trades.slice(0, maxLimit);

  function renderTable(limit) {
    tableBody.innerHTML = ""; // 테이블 초기화
    limitedTrades.slice(0, limit).forEach(trade => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${trade.date !== "N/A" ? trade.date : "-"}</td>
        <td><div class="logomm"><img class="choicelogo" src="${stockLogo(trade.stock_name)}">${trade.stock_name}</div></td>
        <td>${trade.price !== "N/A" ? trade.price.toLocaleString() : "-"}원</td>
        <td>${trade.quantity !== "N/A" ? trade.quantity.toLocaleString() : "-"}주</td>
        <td>${trade.type === "현금매수" ? "매수" : "매도"}</td>
      `;
      tableBody.appendChild(row);
    });

    // "더보기" 버튼 처리
    if (limitedTrades.length > maxVisible) {
      hisLoadMoreBtn.style.display = "block"; // 더보기 버튼 표시
      hisLoadMoreBtn.textContent = showingAll ? "숨기기" : "더보기";
    } else {
      hisLoadMoreBtn.style.display = "none"; // 데이터가 적으면 버튼 숨김
    }
  }

  // 초기 5개만 표시
  renderTable(maxVisible);

  // "더보기" 버튼 클릭 이벤트
  hisLoadMoreBtn.onclick = function () {
    showingAll = !showingAll;
    renderTable(showingAll ? maxLimit : maxVisible);
  };
}

document.addEventListener("DOMContentLoaded", function () {
  const tableBody = document.getElementById("notbuy-tbody");

  tableBody.addEventListener("click", async function (event) {
    if (event.target.classList.contains("cancel-order-btn")) {
      const orderNumber = event.target.value;

      if (!orderNumber) {
        alert("주문 번호를 찾을 수 없습니다.");
        return;
      }

      const confirmCancel = confirm("정말 이 주문을 취소하시겠습니까?");
      if (!confirmCancel) return;

      try {
        // ✅ FastAPI 메인 서버로 주문 취소 요청
        const response = await fetch("/api/cancel-order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order_number: orderNumber }),
        });

        const data = await response.json();

        if (data.success) {
          alert("주문이 취소되었습니다.");
          fetchAccountInfo(); // ✅ UI 갱신 (미체결 내역 다시 가져오기)
        } else {
          alert(`주문 취소 실패: ${data.message}`);
        }
      } catch (error) {
        console.error("주문 취소 중 오류 발생:", error);
        alert("주문 취소 중 오류가 발생했습니다.");
      }
    }
  });
});

// 비밀번호 확인

const password1 = document.getElementById('update-password');
const password2 = document.getElementById('password-check');

function passwordComp() {
    if (password1.value == password2.value) {
        password1.style = "border: 1px solid #00ff00";
        password2.style = "border: 1px solid #00ff00";
    } else {
        password1.style = "border: 1px solid #ff0000";
        password2.style = "border: 1px solid #ff0000";
    }
};

password1.addEventListener("input", passwordComp);
password2.addEventListener("input", passwordComp);
