
  document.getElementById('loginButton').addEventListener('click', () => {
    window.location.href = '/login'; // 로그인 페이지 URL
  });
  
  // 화면 다크모드(상시)
  document.querySelector('.text-bg-primary').style.backgroundColor = '#FF69B4';

  
  // 로그인시 관심종목과  자동매매 보여주는 함수
// document.addEventListener('DOMContentLoaded', () => {
//   // 서버에서 로그인 상태 확인
//   fetch('/api/check-login')
//     .then(response => response.json())
//     .then(data => {
//       if (data.isLoggedIn) {
//         // 로그인 상태일 때 관심종목과 자동매매 섹션 표시
//         loginButton.textContent = `${data.user.name} (로그아웃)`;
//         loginButton.id = 'logoutButton';  // ID를 'logoutButton'으로 변경
//         document.getElementById('favorites').style.display = 'block';
//         document.getElementById('auto-trading').style.display = 'block';

//         logoutButton.addEventListener('click', () => {
//             fetch('/logout', { method: 'POST' })
//               .then(() => {
//                 window.location.href = '/main';
//               })
//               .catch(error => console.error('Error:', error));
//           });
//         } else {
//           // 비로그인 상태일 때 버튼 텍스트와 ID 변경
//           loginButton.textContent = '로그인';
//           loginButton.id = 'loginButton';  // ID를 'loginButton'으로 변경
//         }
//       })
//       .catch(error => console.error('Error:', error));
//   });

document.addEventListener('DOMContentLoaded', () => {
  // 서버에서 로그인 상태 확인
  fetch('/api/check-login')
    .then(response => response.json())
    .then(data => {
      if (data.isLoggedIn) {
        // 로그인 상태일 때 관심종목과 자동매매 섹션 표시
        document.getElementById('favorites').style.display = 'block';
        document.getElementById('auto-trading').style.display = 'block';

        // 기존 로그인 버튼 제거
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
          loginButton.remove();
        }

        // 새로 생성된 로그아웃 버튼
        const logoutButton = document.createElement('button');
        logoutButton.textContent = `${data.user.name} (로그아웃)`;
        logoutButton.classList.add('btn', 'btn-primary');
        logoutButton.id = 'logoutButton';

        // 새 버튼을 원하는 위치에 추가
        const buttonContainer = document.getElementById('buttonContainer'); // 버튼을 추가할 컨테이너 아이디
        buttonContainer.appendChild(logoutButton);

        // 로그아웃 버튼 클릭 시
        logoutButton.addEventListener('click', () => {
          fetch('/logout', { method: 'POST' })
            .then(() => {
              window.location.href = '/main';
            })
            .catch(error => console.error('Error:', error));
        });

      }
    })
    .catch(error => console.error('Error:', error));
});
