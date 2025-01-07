
  document.getElementById('loginButton').addEventListener('click', () => {
    window.location.href = 'login.html'; // 로그인 페이지 URL
  });
  
  document.querySelector('.text-bg-primary').style.backgroundColor = '#FF69B4';

  
  // 로그인시 관심종목과  자동매매 보여주는 함수
document.addEventListener('DOMContentLoaded', () => {
  // 서버에서 로그인 상태 확인
  fetch('/api/check-login')
    .then(response => response.json())
    .then(data => {
      if (data.isLoggedIn) {
        // 로그인 상태일 때 관심종목과 자동매매 섹션 표시
        document.getElementById('favorites').classList.remove('hidden');
        document.getElementById('auto-trading').classList.remove('hidden');
      } else {
        // 비로그인 상태일 때 로그인 페이지로 리다이렉트
        window.location.href = '/login';
      }
    })
    .catch(error => console.error('Error:', error));
});