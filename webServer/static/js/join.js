// 메인 페이지 이동
document.getElementById("logo").addEventListener("click", function () {
    window.location.href = "/"; 
  });

// 회원가입 버튼 활성화
const sighupForm = document.getElementById('sighupForm');
const inputs = sighupForm.querySelectorAll('input[type=text], input[type=email], input[type=password]')
const checkBox = document.getElementById('check');
const sighUpButton = document.getElementById('sighUpButton');

function checkFrom(){
    const allfilled = Array.from(inputs).every(input => input.value.trim() !== "");
    const checkBoxChecked = checkBox.checked;
    
    if (allfilled && checkBoxChecked){
        sighUpButton.disabled = false;
    } else {
        sighUpButton.disabled = true;
    }
}

inputs.forEach(input => {
    input.addEventListener("input", checkFrom);
});
checkBox.addEventListener("change", checkFrom);


// 비밀번호 확인
const password1 = document.getElementById('password');
const password2 = document.getElementById('confirm-password');

function passwordComp(){
    if(password1.value == password2.value){
        password1.style = "border: 1px solid #00ff00";
        password2.style = "border: 1px solid #00ff00";
    }else{
        password1.style = "border: 1px solid #ff0000";
        password2.style = "border: 1px solid #ff0000";
    }
};

password1.addEventListener("input", passwordComp);
password2.addEventListener("input", passwordComp);

