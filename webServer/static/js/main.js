document.getElementById('loginButton').addEventListener('click', () => {
  window.location.href = '/login'; // 로그인 페이지 URL
});

<<<<<<< HEAD
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
=======
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
    .catch(error => console.error('Error:', error));
});

// 화면 다크모드(상시)
document.querySelector('.text-bg-primary').style.backgroundColor = '#FF69B4';
>>>>>>> b3486326c0bdf6b4f98df720e5dbf4654dd04f69


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
<<<<<<< HEAD
        // 기존 로그인 버튼 제거
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
          loginButton.remove();
        }
        const mypageButton = document.createElement('button');
        mypageButton.textContent = `마이 페이지`;
        mypageButton.classList.add('btn', 'btn-primary');
        mypageButton.id = 'mypageButton';

        // 새 버튼을 원하는 위치에 추가
        const buttonContainer = document.getElementById('buttonContainer'); // 버튼을 추가할 컨테이너 아이디
        buttonContainer.appendChild(mypageButton);

        // 마이페이지 버튼 클릭 시
        mypageButton.addEventListener('click', () => {
          window.location.href = '/mypage'; // 로그인 페이지 URL
        });

        // 새로 생성된 로그아웃 버튼
        const logoutButton = document.createElement('button');
        logoutButton.textContent = `로그아웃`;
        logoutButton.classList.add('btn', 'btn-primary');
        logoutButton.id = 'logoutButton';

        // 새 버튼을 원하는 위치에 추가가
        buttonContainer.appendChild(logoutButton);

        // 로그아웃 버튼 클릭 시
        logoutButton.addEventListener('click', () => {
          fetch('/logout', { method: 'POST' })
            .then(() => {
              window.location.href = '/main';
            })
            .catch((error) => console.error('Error:', error));
        });
=======
        document.getElementById('loginButton').style.display = 'none';
        document.getElementById('logoutButton').style.display = 'block';
        document.getElementById('mypageButton').style.display = 'block';

>>>>>>> b3486326c0bdf6b4f98df720e5dbf4654dd04f69
      }
    })
    .catch((error) => console.error('Error:', error));
});
