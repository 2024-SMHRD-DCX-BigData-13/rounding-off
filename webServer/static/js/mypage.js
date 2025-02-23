/* Optimized JavaScript for My Page Functionality */

/* ===============================
   Utility Functions
=============================== */
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

function generateRandomColors(count) {
  const colors = [];
  for (let i = 0; i < count; i++) {
    const randomColor = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
    colors.push(randomColor);
  }
  return colors;
}

/* ===============================
   Logo Click & Password Comparison
=============================== */
// 로고 클릭 시 홈으로 이동
document.getElementById("logo")?.addEventListener("click", () => {
  window.location.href = "/";
});

// 비밀번호 일치 여부에 따라 테두리 색 변경
const password1 = document.getElementById("update-password");
const password2 = document.getElementById("password-check");
function passwordComp() {
  if (password1.value === password2.value) {
    password1.style.border = "1px solid #00ff00";
    password2.style.border = "1px solid #00ff00";
  } else {
    password1.style.border = "1px solid #ff0000";
    password2.style.border = "1px solid #ff0000";
  }
}
password1?.addEventListener("input", passwordComp);
password2?.addEventListener("input", passwordComp);

/* ===============================
   UI Update Functions
=============================== */
// [1] 거래 내역 UI 업데이트  
// "더보기" 버튼 클릭 시 이미 생성된 행들을 추가/제거하여 기존 행들의 위치를 유지
function updateTradeHistoryUI(trades) {
  const tableBody = document.getElementById("trade-table-body");
  const loadMoreBtn = document.getElementById("his-load-more-btn");
  if (!tableBody || !loadMoreBtn) {
    console.error("Trade history UI elements not found.");
    return;
  }
  
  const maxLimit = 20;   // 최대 렌더링 건수
  const maxVisible = 5;  // 처음에 보여줄 건수
  
  // 최신 거래 내역이 위로 오도록 역순 정렬 후 최대 maxLimit 건 사용
  const sortedTrades = trades.slice().slice(0, maxLimit);

  function formatDate(dateStr) {
    if (!dateStr || dateStr.length !== 8) return "-";
    return `${dateStr.slice(0,4)}/${dateStr.slice(4,6)}/${dateStr.slice(6,8)}`;
  }
  
  // 각 행을 미리 생성하여 배열에 저장
  const rows = sortedTrades.map(trade => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${trade.order_date !== "" ? formatDate(trade.order_date) : "-"}</td>
      <td style="text-align: center; vertical-align: middle; width: 25%;">
        <div class="logomm">
          <img class="choicelogo" src="${stockLogo(trade.stock_name)}" alt="${trade.stock_name} Logo">
          ${trade.stock_name}
        </div>
      </td>
      <td class="trade_price">${trade.price !== "0" ? Number(trade.price).toLocaleString() + "원" : "-"}</td>
      <td>${trade.quantity !== "0" ? Number(trade.quantity).toLocaleString() + "주" : "-"}</td>
      <td>${trade.type === "현금매수" ? "매수" : "매도"}</td>
    `;
    return row;
  });
  
  // 초기 렌더링: tableBody에 처음 maxVisible 행만 추가
  tableBody.innerHTML = "";
  for (let i = 0; i < maxVisible && i < rows.length; i++) {
    tableBody.appendChild(rows[i]);
  }
  
  // "더보기" 버튼 노출 여부
  if (rows.length > maxVisible) {
    loadMoreBtn.style.display = "block";
    loadMoreBtn.textContent = "더보기";
  } else {
    loadMoreBtn.style.display = "none";
  }
  
  // 토글 상태 변수
  let showingAll = false;
  
  loadMoreBtn.onclick = () => {
    if (!showingAll) {
      // 나머지 행들을 순서대로 추가
      for (let i = maxVisible; i < rows.length; i++) {
        tableBody.appendChild(rows[i]);
      }
      loadMoreBtn.textContent = "숨기기";
    } else {
      // maxVisible 이후 행들을 제거
      while (tableBody.children.length > maxVisible) {
        tableBody.removeChild(tableBody.lastElementChild);
      }
      loadMoreBtn.textContent = "더보기";
    }
    showingAll = !showingAll;
  };
}

// [2] 계좌 정보 UI 업데이트 (총 수익률 포함)
function updateAccountUI(account, totalProfitRate) {
  const accountNumberElem = document.getElementById("account-number");
  const balanceElem = document.getElementById("balance");
  const profitRateElem = document.getElementById("total-profit-rate");
  if (!accountNumberElem || !balanceElem || !profitRateElem) {
    console.error("Account UI elements not found.");
    return;
  }
  accountNumberElem.textContent = account.account_number || "-";
  balanceElem.textContent = account.balance ? account.balance.toLocaleString() + "원" : "-";
  profitRateElem.textContent =
    (totalProfitRate !== null && totalProfitRate !== undefined)
      ? totalProfitRate.toFixed(2) + "%"
      : "-";
      const profitRateText = profitRateElem.textContent; // 또는 innerText 사용
      const profitNumber = parseFloat(profitRateText.replace(/[^0-9.-]/g, ""));
      // 기존 클래스를 먼저 모두 제거 (원하는 경우)
      profitRateElem.classList.remove("positive-profit", "negative-profit");
      
      if (profitNumber < 0) {
        profitRateElem.classList.add("negative-profit");
      } else if (profitNumber > 0) {
        profitRateElem.classList.add("positive-profit");
      }

}

// [3] 미체결 내역 UI 업데이트
function updatePendingOrdersUI(orders) {
  const tableBody = document.getElementById("notbuy-tbody");
  const loadMoreBtn = document.getElementById("pending-load-more-btn");
  if (!tableBody || !loadMoreBtn) {
    console.error("Pending orders UI elements not found.");
    return;
  }
  tableBody.innerHTML = "";
  const filteredOrders = (Array.isArray(orders) ? orders : []).filter(
    order => order.price && order.status !== "체결"
  );
  if (filteredOrders.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;">미체결 내역 없음</td></tr>`;
    loadMoreBtn.style.display = "none";
    return;
  }
  const maxVisible = 5;
  let showingAll = false;
  const renderTable = (limit) => {
    tableBody.innerHTML = "";
    filteredOrders.slice(0, limit).forEach(order => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>
          <img class="choicelogo" src="${stockLogo(order.stock_name)}" alt="${order.stock_name} Logo">
          ${order.stock_name || "-"}
        </td>
        <td>${order.price ? Number(order.price).toLocaleString() + "원" : "-"}</td>
        <td>${order.quantity ? Number(order.quantity).toLocaleString() + "주" : "-"}</td>
        <td>${order.status || "-"}</td>
      `;
      tableBody.appendChild(row);
    });
    if (filteredOrders.length > maxVisible) {
      loadMoreBtn.style.display = "block";
      loadMoreBtn.textContent = showingAll ? "숨기기" : "더보기";
    } else {
      loadMoreBtn.style.display = "none";
    }
  };
  renderTable(maxVisible);
  loadMoreBtn.onclick = () => {
    showingAll = !showingAll;
    renderTable(showingAll ? filteredOrders.length : maxVisible);
  };
}

// [4] 보유 종목 테이블 업데이트 및 총 수익률 계산  
// 차트 업데이트 호출은 제거하고, 보유 종목 데이터는 전역 변수(window.holdingsData)에 저장
function updateHoldingsTable(stocks) {
  const tableBody = document.getElementById("my-stocks-table");
  if (!tableBody) {
    console.error("Holdings table element not found.");
    return;
  }
  tableBody.innerHTML = "";
  let totalProfit = 0;
  let totalInvestment = 0;
  stocks.forEach(stock => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>
        <div class="logomm">
          <img class="choicelogo" src="${stockLogo(stock.stock_name)}" alt="${stock.stock_name} Logo">
          ${stock.stock_name}
        </div>
      </td>
      <td>${stock.current_price.toLocaleString()}원</td>
      <td>${stock.evaluation_profit.toLocaleString()}원</td>
      <td>${stock.buy_price.toLocaleString()}원</td>
      <td>${stock.quantity}주</td>
    `;
    tableBody.appendChild(row);
    totalProfit += stock.evaluation_profit;
    totalInvestment += stock.buy_price * stock.quantity;
  });
  const totalProfitRate = totalInvestment > 0 ? (totalProfit / totalInvestment) * 100 : null;
  // 계좌 정보 업데이트 시 총 수익률도 함께 반영
  fetchAccountInfo(totalProfitRate);
  document.querySelectorAll("tbody tr td:nth-child(3)").forEach(cell => {
    const profitNumber = parseFloat(cell.textContent.replace(/[^0-9.-]/g, ""));
    if (profitNumber > 0) {
      cell.classList.add("positive-profit");
    } else if (profitNumber < 0) {
      cell.classList.add("negative-profit");
    }
  });
  // 보유 종목 데이터는 전역 변수에 저장 (차트는 로딩 완료 후에 그립니다)
  window.holdingsData = stocks;
}

function updateHoldingsChart(stocks) {
  // 그룹화를 위한 객체 생성: 종목명별 누적 값 계산
  const aggregated = {};
  stocks.forEach(stock => {
    const name = stock.stock_name;
    // current_price와 quantity가 숫자여야 함. (만약 문자열이면 parseFloat 등을 사용)
    const value = Number(stock.current_price) * Number(stock.quantity);
    if (aggregated[name]) {
      aggregated[name] += value;
    } else {
      aggregated[name] = value;
    }
  });

  // 고유 종목명과 누적값 배열 생성
  const labels = Object.keys(aggregated);
  const values = Object.values(aggregated);

  // 고정된 보라색 계열 색상 배열 (필요에 따라 추가)
  const Colors = ['#8E44AD', '#3498DB', '#E74C3C', '#27AE60', '#F1C40F', '#9B59B6', '#34495E', '#16A085', '#D35400', '#2ECC71'];
  // 항목 수에 맞게 색상을 순환 사용
  const backgroundColors = labels.map((_, idx) => Colors[idx % Colors.length]);

  const canvas = document.getElementById("accountPieChart");
  if (!canvas) {
    console.error("Chart canvas element with id 'accountPieChart' not found.");
    return;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    console.error("2D context could not be obtained from the canvas.");
    return;
  }

  // 최초 생성 시 (window.myPieChart가 없을 경우)에는 애니메이션 포함
  if (!window.myPieChart) {
    window.myPieChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [{
          label: "종목별 비중",
          data: values,
          backgroundColor: backgroundColors,
          borderColor: "#ffffff",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        animation: {
          duration: 1000 // 초기 생성 시 1초 애니메이션
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: "#cfcfcf",
              font: { size: 14 }
            }
          }
        }
      }
    });
    console.log("차트가 생성되었습니다.");
  } else {
    // 업데이트 시 애니메이션 없이 값만 반영
    window.myPieChart.data.labels = labels;
    window.myPieChart.data.datasets[0].data = values;
    window.myPieChart.data.datasets[0].backgroundColor = backgroundColors;
    window.myPieChart.options.animation.duration = 0; // 업데이트 시 애니메이션 없음
    window.myPieChart.update();
    console.log("차트가 업데이트되었습니다.");
  }
}



/* ===============================
   Fetch Functions (API Calls)
=============================== */
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

async function fetchHoldings() {
  try {
    const response = await fetch("/account/holdings");
    const data = await response.json();
    if (data.status === "success") {
      const stocks = data.data;
      updateHoldingsTable(stocks);
      console.log("보유 종목 데이터 로드 완료");
      // 필요시 차트 업데이트 함수도 호출합니다.
      // updateHoldingsChart(stocks);
    } else {
      console.error("보유 종목 데이터 로드 실패:", data.detail);
    }
  } catch (error) {
    console.error("보유 종목 데이터 요청 오류:", error);
  }
}

// DOMContentLoaded 이후 5초마다 fetchHoldings()를 호출
document.addEventListener("DOMContentLoaded", () => {
  // 최초 호출
  fetchHoldings();
  // 5초(5000ms)마다 호출
  setInterval(fetchHoldings, 5000);
});


async function fetchTradeHistory() {
  try {
    const response = await fetch("/account/trade-history");
    const data = await response.json();
    if (data.status === "success") {
      updateTradeHistoryUI(data.data);
    } else {
      console.error("거래 내역 데이터 로드 실패:", data.detail);
    }
  } catch (error) {
    console.error("거래 내역 데이터 요청 오류:", error);
  }
}

async function checkLoginStatus() {
  try {
    const response = await fetch("/api/check-login", { method: "GET", credentials: "include" });
    if (!response.ok) {
      throw new Error(`HTTP 오류: ${response.status}`);
    }
    const data = await response.json();
    const nameElement = document.getElementById("name");
    const emailElement = document.getElementById("email");
    const telElement = document.getElementById("tel");
    const nameField = document.getElementById("update-name");
    const emailField = document.getElementById("update-email");
    const telField = document.getElementById("update-phone");
    if (data.isLoggedIn) {
      nameElement.textContent = data.user.name;
      emailElement.textContent = data.user.email;
      telElement.textContent = data.user.tel;
      if (nameField) nameField.value = data.user.name;
      if (emailField) emailField.value = data.user.email;
      if (telField) telField.value = data.user.tel;
    } else {
      nameElement.textContent = "로그인이 필요합니다.";
    }
  } catch (error) {
    console.error("로그인 상태 확인 중 오류 발생:", error);
  }
}

/* ===============================
   Navigation & Modal Setup
=============================== */
function setupScrollNavigation() {
  const profileSection = document.getElementById("profile-section");
  const holdings = document.getElementById("holdings");
  const tradeSection = document.getElementById("trade-section");
  const notbuy = document.getElementById("notbuy");
  document.getElementById("goProfile")?.addEventListener("click", () => {
    profileSection?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  document.getElementById("goNotBuy")?.addEventListener("click", () => {
    notbuy?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  document.getElementById("goHoldings")?.addEventListener("click", () => {
    holdings?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  document.getElementById("goTrade")?.addEventListener("click", () => {
    tradeSection?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function setupProfileUpdate() {
  const editProfileButton = document.getElementById("editProfileButton");
  const modal = document.getElementById("editProfileModal");
  const closeButton = document.querySelector(".close-button");
  if (editProfileButton && modal && closeButton) {
    editProfileButton.addEventListener("click", () => (modal.style.display = "block"));
    closeButton.addEventListener("click", () => (modal.style.display = "none"));
    window.addEventListener("click", (event) => {
      if (event.target === modal) modal.style.display = "none";
    });
  }
  const updateProfileForm = document.getElementById("updateProfileForm");
  const passwordInput = document.getElementById("update-password");
  const passwordCheckInput = document.getElementById("password-check");
  const telInput = document.getElementById("update-phone");
  const sessionPassword = document.body.dataset.sessionPassword;
  updateProfileForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const updatedData = {
      email: document.getElementById("update-email").value.trim(),
      password: passwordInput.value.trim(),
      tel: telInput.value.trim()
    };
    if (!updatedData.email || !updatedData.password || !updatedData.tel) {
      alert("모든 필드를 올바르게 입력하세요.");
      return;
    }
    if (passwordInput.value.trim() !== passwordCheckInput.value.trim()) {
      alert("비밀번호가 일치하지 않습니다. 다시 확인해주세요.");
      passwordInput.focus();
      return;
    }
    if (sessionPassword && passwordInput.value.trim() === sessionPassword) {
      alert("기존 비밀번호와 동일합니다. 다른 비밀번호를 입력해주세요.");
      passwordInput.focus();
      return;
    }
    try {
      const response = await fetch("/api/update-user-info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData)
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "알 수 없는 오류가 발생했습니다.");
      }
      const data = await response.json();
      if (data.success) {
        alert("회원정보가 성공적으로 수정되었습니다.");
        modal.style.display = "none";
        location.reload();
      } else {
        alert(`회원정보 수정 실패: ${data.message}`);
      }
    } catch (error) {
      console.error("회원정보 수정 중 오류 발생:", error);
      alert(`오류 발생: ${error.message}`);
    }
  });
}

document.getElementById("logoutButton")?.addEventListener("click", () => {
  fetch("/logout", { method: "POST" })
    .then(() => (window.location.href = "/main"))
    .catch((error) => console.error("Error:", error));
});

/* ===============================
   Initialization on DOMContentLoaded
=============================== */

// 로딩 화면 관련 처리: total-profit-rate 요소의 텍스트가 채워지면 로딩 숨기고 콘텐츠 표시 후 차트 업데이트
const tdV = document.getElementById('total-profit-rate');
function loading () {
  if (tdV.textContent.trim() !== ""){
    const loadingElem = document.getElementById("loading");
    const contentElem = document.getElementById("content");
    loadingElem.style.display = "none"; // 로딩 화면 숨김
    contentElem.style.display = "block"; // 실제 콘텐츠 표시
    
    // 전역 변수에 보유 종목 데이터가 있으면 차트 그리기
    if (window.holdingsData) {
      updateHoldingsChart(window.holdingsData);
    } else {
      console.warn("보유 종목 데이터가 없어 차트를 그릴 수 없습니다.");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupProfileUpdate();
  setupScrollNavigation();
  checkLoginStatus();
  fetchHoldings();
  fetchTradeHistory();
});
const observer = new MutationObserver(loading);
observer.observe(tdV, { childList: true, subtree: true, characterData: true });

const deleteBtn = document.getElementById("deleteProfileButton");
if (deleteBtn) {
  deleteBtn.addEventListener("click", function() {
    if (confirm("정말 탈퇴하시겠습니까?")) {
      // 페이지에 표시된 이메일을 가져옵니다.
      const emailElem = document.getElementById("email");
      const email = emailElem ? emailElem.textContent.trim() : "";
      
      // 회원 탈퇴 엔드포인트로 DELETE 요청 전송 (요청 본문에 이메일 포함)
      fetch("/delete-profile", {
        method: "POST", // 필요에 따라 POST 등으로 변경 가능
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "include", // 쿠키나 인증 정보가 필요하다면 포함
        body: JSON.stringify({ email: email })
      })
      .then(response => {
        if (response.ok) {
          alert("회원 탈퇴가 완료되었습니다.");
          window.location.href = "/"; // 탈퇴 후 리다이렉트할 주소
        } else {
          alert("회원 탈퇴에 실패했습니다. 잠시 후 다시 시도해주세요.");
        }
      })
      .catch(error => {
        console.error("회원 탈퇴 요청 중 오류 발생:", error);
        alert("회원 탈퇴 중 오류가 발생했습니다.");
      });
    }
  });
}