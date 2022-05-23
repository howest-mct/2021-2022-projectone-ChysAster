const lanIP = `${window.location.hostname}:5000`;
const socket = io(`http://${lanIP}`);



const listenToSocket = function () {
  socket.on("connected", function () {
    console.log("verbonden met socket webserver");
  });

  

};

document.addEventListener("DOMContentLoaded", function () {
  console.info("DOM geladen");
  // listenToUI();
  listenToSocket();
});
