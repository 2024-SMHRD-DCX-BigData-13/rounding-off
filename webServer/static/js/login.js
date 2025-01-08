
// 로고 클릭 시 메인 페이지로 이동하는 함수

document.getElementById("logo").addEventListener("click", function () {
    window.location.href = "/"; 
  });


   // 로그인확인함수
  document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('form');
  
    loginForm.addEventListener('submit', (event) => {
      event.preventDefault(); // 기본 폼 제출 방지
  
      // 사용자 입력값 가져오기
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
  
      // 서버로 POST 요청 보내기
      fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      })
        .then((response) => {
          if (response.ok) {
            // 로그인 성공 시 메인 페이지로 이동
            window.location.href = '/main';
          } else {
            // 로그인 실패 시 에러 메시지 표시
            return response.text().then((message) => {
              alert(`로그인 실패: ${message}`);
            });
          }
        })
        .catch((error) => {
          console.error('Error:', error);
          alert('서버와의 연결에 문제가 발생했습니다.');
        });
    });
  });