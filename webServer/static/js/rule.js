document.querySelectorAll('input[name="agree"]').forEach((radio) => {
    radio.addEventListener("click", function () {
      const value = this.value;
  
      if (value === "yes") {
        window.opener.setAgreement(true);
        window.close();
      } else if (value === "no") {
        alert("약관에 동의하지 않으면 진행할 수 없습니다.");
        window.close();
      }
    });
  });
  