// 데이터를 FastAPI 서버에서 가져옵니다.
// fetch("/kiwoom-data")
//     .then(response => response.json())
//     .then(data => {
//         if (data.error) {
//             alert(data.error);
//             return;
//         }

//         const stockData = data.data;

//         // 날짜와 종가 데이터를 추출합니다.
//         const labels = stockData.map(item => item.date).reverse(); // 날짜를 역순으로 정렬
//         const closePrices = stockData.map(item => item.close).reverse();

//         // Chart.js로 차트 생성
//         const ctx = document.getElementById('stockChart').getContext('2d');
//         new Chart(ctx, {
//             type: 'line',
//             data: {
//                 labels: labels,
//                 datasets: [{
//                     label: 'Close Price',
//                     data: closePrices,
//                     borderColor: 'rgba(75, 192, 192, 1)',
//                     borderWidth: 2,
//                     fill: false,
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 plugins: {
//                     legend: {
//                         display: true,
//                         position: 'top'
//                     }
//                 },
//                 scales: {
//                     x: {
//                         display: true,
//                         title: {
//                             display: true,
//                             text: 'Date'
//                         }
//                     },
//                     y: {
//                         display: true,
//                         title: {
//                             display: true,
//                             text: 'Close Price'
//                         }
//                     }
//                 }
//             }
//         });
//     })
//     .catch(error => console.error('Error fetching stock data:', error));
