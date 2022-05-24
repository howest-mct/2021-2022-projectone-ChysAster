const lanIP = `${window.location.hostname}:5000`;
const socket = io(`http://${lanIP}`);



const listenToSocket = function () {
  socket.on("connected", function () {
    console.log("verbonden met socket webserver");
  });

  socket.on('B2F_status_temp', function (jsonObject) {
        console.log(jsonObject)
        document.querySelector('.js-temperatuur').innerHTML = `Temperatuur: ${jsonObject.data} &deg; C `
    })
  

};

document.addEventListener("DOMContentLoaded", function () {
  console.info("DOM geladen");
  // listenToUI();
  listenToSocket();
});
