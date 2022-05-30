'use strict'
const lanIP = `${window.location.hostname}:5000`;
console.log(lanIP)
const socket = io(`http://${lanIP}`);

//#region ***  DOM references                           ***********
let htmlHistoriek;
//#endregion

//#region ***  Callback-Visualisation - show___         ***********
const showHistoriek = function (jsonObject) {
  console.log(jsonObject)
  let htmlString = '';
  for (const historiek of jsonObject.historiek) {
    htmlString += `<table>
          <tr>
            <th>id</th>
            <th>Device</th>
            <th>Tijdstip</th>
            <th>Waarde</th>
          </tr>
          <tr class="js-historiek">
            <td>${historiek.idHistoriek}</td>
            <td>${historiek.naam}</td>
            <td>${historiek.tijdstip}</td>
            <td>${historiek.waarde}</td>
          </tr>
        </table>`
  }

  htmlHistoriek.innerHTML = htmlString;
  
}
//#endregion

//#region ***  Data Access - get___                     ***********
const getHistoriek = function () {
  handleData(`http://${lanIP}/api/v1/historiek/`, showHistoriek);
}

//#endregion

//#region ***  Event Listeners - listenTo___            ***********
const listenToSocket = function () {
  socket.on("connected", function () {
    console.log("verbonden met socket webserver");
  });

  socket.on('B2F_status_temp', function (jsonObject) {
        console.log("in socket")
        console.log(jsonObject)
        document.querySelector('.js-temperatuur').innerHTML = `${jsonObject.data} &deg; C`
    })
  

};
//#endregion

//#region ***  Init / DOMContentLoaded                  ***********
document.addEventListener("DOMContentLoaded", function () {
  console.info("DOM geladen");

  htmlHistoriek = document.querySelector('.historiek')
  // listenToUI();
  listenToSocket();
  getHistoriek();
});
//#endregion