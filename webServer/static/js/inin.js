// // 서버 URL
// const serverUrl = "http://127.0.0.1:8000/api/receive_data";

// // 데이터를 서버로 전송하는 함수
// async function executePostRequest(data) {
//   try {
//     const response = await fetch(serverUrl, {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(data),
//     });

//     if (response.ok) {
//       const responseData = await response.json();
//       console.log("서버 응답:", responseData);
//     } else {
//       console.error("서버 응답 오류:", response.status, response.statusText);
//     }
//   } catch (error) {
//     console.error("요청 중 오류 발생:", error);
//   }
// }

// // 페이지 로드 시 실행
// window.onload = () => {
//   const dataToSend = [
//     { date: "20240101", open: 100000, high: 102000, low: 99000, close: 101000, volume: 15000 },
//     { date: "20240102", open: 101000, high: 103000, low: 100000, close: 102000, volume: 20000 },
//   ];

//   console.log("데이터 전송 중...");
//   executePostRequest(dataToSend);
// };
