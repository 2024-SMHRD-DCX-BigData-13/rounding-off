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

// 화면 다크모드(상시)
document.querySelector('.text-bg-primary').style.backgroundColor = '#FF69B4';

document.addEventListener('DOMContentLoaded', () => {
  // 서버에서 로그인 상태 확인
  fetch('/api/check-login')
    .then((response) => response.json())
    .then((data) => {
      if (data.isLoggedIn) {
        // 로그인 상태일 때 관심종목과 자동매매 섹션 표시
        document.getElementById('favorites').style.display = 'block';
        document.getElementById('auto-trading').style.display = 'block';
        // document.getElementsByClassName('intro').style.display = 'none';
        document.getElementById('loginButton').style.display = 'none';
        document.getElementById('logoutButton').style.display = 'block';
        document.getElementById('mypageButton').style.display = 'block';
      }
    })
    .catch((error) => console.error('Error:', error));
});
