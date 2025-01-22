// 메인 페이지 이동
document.getElementById("logo").addEventListener("click", function () {
    window.location.href = "/";
});

// 회원가입 버튼 활성화
const sighupForm = document.getElementById('sighupForm');
const inputs = sighupForm.querySelectorAll('input[type=text], input[type=email], input[type=password], input[type=tel]');
const checkBox = document.getElementById('check');
const sighUpButton = document.getElementById('sighUpButton');

function checkFrom() {
    const allfilled = Array.from(inputs).every(input => input.value.trim() !== "");
    const checkBoxChecked = checkBox.checked;

    if (allfilled && checkBoxChecked) {
        sighUpButton.disabled = false;
    } else {
        sighUpButton.disabled = true;
    }
}

inputs.forEach(input => {
    input.addEventListener("input", checkFrom);
});



// 비밀번호 확인
const password1 = document.getElementById('password');
const password2 = document.getElementById('confirm-password');

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


document.getElementById("ruleLink").addEventListener("click", function (event) {
    event.preventDefault();
    const popupWidth = 800;
    const popupHeight = 760;

    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;

    const left = window.screenX + (screenWidth - popupWidth) / 2;
    const top = window.screenY + (screenHeight - popupHeight) / 2;

    window.open(
        "/rule",
        "약관동의",
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=no,scrollbars=no`
    );
    window.setAgreement = function (agreed) {
        const checkbox = document.getElementById("check");
        if (agreed) {
            checkbox.checked = true;
            checkbox.disabled = false;
            checkFrom();
        }
        window.close();
    };
    

});

// email 중복체크
const email = document.getElementById('email');
email.addEventListener('input', () => {
    const emailV = email.value.trim();

    // 서버로 POST 요청 보내기
    fetch('/emailCheck', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `email=${encodeURIComponent(emailV)}`,
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error('서버 응답 에러');
            }
            return response.json(); // JSON 데이터로 변환
        })
        .then((data) => {
            // 서버에서 받은 데이터 처리
            if (data.exists) {
                email.style = "border: 1px solid #00ff00"; // 빨간색 테두리
            } else {
                email.style = "border: 1px solid #ff0000"; // 초록색 테두리
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('서버와의 연결에 문제가 발생했습니다.');
        });
});

