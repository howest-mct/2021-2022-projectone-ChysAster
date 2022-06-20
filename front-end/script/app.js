'use strict';
const lanIP = `${window.location.hostname}:5000`;
console.log(lanIP);
const socket = io(`http://${lanIP}`);

let htmlStringBlauw = '';
let htmlStringGeel = '';
//#region ***  DOM references                           ***********
let htmlHistoriek, htmlIndex, htmlOpdracht, htmlBeginner, htmlOpdrachtBlauw, htmlOpdrachtGeel, htmlGespeeldBlauw, htmlGespeeldGeel, htmlProcent;
//#endregion
let kleur = '';
let huidige_opdracht_geel = '';
let huidige_opdracht_blauw = '';
let aantal_minuten_geel = 0;
let aantal_minuten_blauw = 0;
let counterBlauw = 0;
let counterGeel = 0;
let idGeel = 0;
let idBlauw = 0;

let grafiekData = [];
let grafiekLabel = [];

//#region ***  4 in a row references                           ***********
let r;
let c;

let laatstGezetteTile = null;
//#endregion

//#region ***  Callback-Visualisation - show___         ***********
const showHistoriek = function (jsonObject) {
  console.log(jsonObject);
  let htmlString = `<table class="c-table w-full table-auto border-spacing-1 border dark:border-gray-900">
      <tr>
        <th class="bg-gray-200 dark:bg-gray-800">Team</th>
        <th class="bg-gray-200 dark:bg-gray-800">Tijdstip</th>
      </tr>`;
  for (const historiek of jsonObject.historiek) {
    let team = historiek.waarde.toUpperCase();
    htmlString += `
          <tr>
            <td class="border border-slate-100 dark:border-slate-900 p-2 text-center">${team}</td>
            <td class="border border-slate-100 dark:border-slate-900 p-2 text-center">${historiek.tijdstip}</td>
          </tr>
        `;
  }
  htmlString += `</table>`;

  htmlHistoriek.innerHTML = htmlString;
};
const showAantalGeel = function (jsonObject) {
  console.log(jsonObject);
  for (const aantal of jsonObject.aantal) {
    console.log(aantal.aantal);
    aantalGespeeldGeel = aantal.aantal;
    yellow(aantalGespeeldGeel);
    console.log(aantalGespeeldGeel);
    htmlStringGeel = `<table class="c-table w-full table-auto border-spacing-1 border dark:border-gray-900">
      <tr>
        <th class="bg-gray-200 dark:bg-gray-800 dark:text-white">Gespeelde spelletjes geel. Aantal: ${aantal.aantal}</th>
      </tr>`;
  }
};

const showGeel = function (jsonObject) {
  console.log(jsonObject);
  for (const spel of jsonObject.spelletjes) {
    htmlStringGeel += `
          <tr>
            <td class="border dark:text-white border-slate-100 dark:border-slate-900 p-2 text-center">${spel.Activiteit}</td>
          </tr>
        `;
  }
  htmlStringGeel += `</table>`;

  htmlGespeeldGeel.innerHTML = htmlStringGeel;
};

const showAantalBlauw = function (jsonObject) {
  console.log(jsonObject);
  for (const aantal of jsonObject.aantal) {
    console.log(aantal.aantal);
    aantalGespeeldBlauw = aantal.aantal;
    blue(aantalGespeeldBlauw);
    console.log(aantalGespeeldBlauw);
    htmlStringBlauw = `<table class="c-table w-full table-auto border-spacing-1 border dark:border-gray-900">
      <tr>
        <th class="bg-gray-200 dark:bg-gray-800 dark:text-white">Gespeelde spelletjes blauw. Aantal: ${aantal.aantal}</th>
      </tr>`;
  }
};

const showBlauw = function (jsonObject) {
  console.log(jsonObject);

  for (const spel of jsonObject.spelletjes) {
    htmlStringBlauw += `
          <tr>
            <td class="border border-slate-100 dark:text-white dark:border-slate-900 p-2 text-center">${spel.Activiteit}</td>
          </tr>
        `;
  }
  htmlStringBlauw += `</table>`;
  htmlGespeeldBlauw.innerHTML = htmlStringBlauw;
};

const showSpelletjes = function (jsonObject) {};
//#endregion

//#region ***  Data Access - get___                     ***********
const getHistoriek = function () {
  handleData(`http://${lanIP}/api/v1/historiek/badges/`, showHistoriek);
};

const getGespeeldGeel = function () {
  handleData(`http://${lanIP}/api/v1/gespeeld/geel/`, showGeel);
};

const getGespeeldBlauw = function () {
  handleData(`http://${lanIP}/api/v1/gespeeld/blauw/`, showBlauw);
};

const getSpelletejs = function () {
  handleData(`http://${lanIP}/api/v1/spelletjes/${kleur}/`, showSpelletjes);
};

const getAantalBlauw = function () {
  handleData(`http://${lanIP}/api/v1/aantal/blauw/`, showAantalBlauw);
};

const getAantalGeel = function () {
  handleData(`http://${lanIP}/api/v1/aantal/geel/`, showAantalGeel);
};

//#endregion

//#region ***  functions 4 in a row                     ***********
const positieKolom = function (number) {
  r = 0;
  c = number;
};

//#endregion

//#region ***  Event Listeners - listenTo___            ***********

const gescand = function () {
  socket.on('B2F_rfid_data', function (jsonObject) {
    handle_gescand(jsonObject);
  });
};

const listenToSocketGame = function () {
  socket.on('B2F_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
};

const listenToSocketTemp = function () {
  socket.on('B2F_status_temp', function (jsonObject) {
    console.log('in socket');
    console.log(jsonObject);
    document.querySelector('.js-temperatuur').innerHTML = `${jsonObject.temperatuur} &deg; C`;
  });

  socket.on('B2F_show_water_icoon', function () {
    console.log('open water ');
    closeCold();
    openWater();
  });

  socket.on('B2F_close_water_icoon', function () {
    console.log('sluit water');
    closeWater();
    openCold();
  });
};

const listenToSocket = function () {
  socket.on('connected', function () {
    console.log('verbonden met socket webserver');
  });

  socket.on('B2F_opdracht_geel', function (jsonObject) {
    huidige_opdracht_geel = jsonObject.Activiteit;
    console.log(huidige_opdracht_geel);
    aantal_minuten_geel = jsonObject.aantalMinuten;
    idGeel = jsonObject.idActiviteiten;
    let hmtlString2 = huidige_opdracht_geel;
    let htmlString = huidige_opdracht_geel;
    htmlOpdracht.innerHTML = htmlString;
    htmlOpdrachtGeel.innerHTML = hmtlString2;
    openGeel();
    openOpdracht();
    socket.emit('F2B_opdracht_geel_is_gespeeld', idGeel);
  });

  socket.on('B2F_opdracht_blauw', function (jsonObject) {
    huidige_opdracht_blauw = jsonObject.Activiteit;
    console.log(huidige_opdracht_blauw);
    aantal_minuten_blauw = jsonObject.aantalMinuten;
    idBlauw = jsonObject.idActiviteiten;
    let htmlString2 = huidige_opdracht_blauw;
    let htmlString = huidige_opdracht_blauw;
    htmlOpdrachtBlauw.innerHTML = htmlString2;
    htmlOpdracht.innerHTML = htmlString;
    openBlauw();
    openOpdracht();
    socket.emit('F2B_opdracht_blauw_is_gespeeld', idBlauw);
  });

  socket.on('B2F_geslaagd_geel', function () {
    console.log('B2F_geslaagd_geel');
    kleur = 'geel';
    openGeslaagd();
  });

  socket.on('B2F_geslaagd_blauw', function () {
    console.log('B2F_geslaagd_blauw');
    kleur = 'blauw';
    openGeslaagd();
  });

  socket.on('B2F_ongedaan_maken', function () {
    verwijderPiece();
  });

  socket.on('B2F_beginner', function (kleuren) {
    document.querySelector('.beginnerShowen').innerHTML = kleuren;
  });
};
//#endregion

const opdrachtGeslaagd = function (geslaagd) {
  console.log('geslaagd: ', geslaagd);
  socket.emit('F2B_opdracht_geslaagd', {
    kleur: kleur,
    geslaagd: geslaagd,
  });
  closeGeslaagd();
};

const newGame = function () {
  socket.emit('F2B_restart_game');
};

//#region ***  4 OP EEN RIJ CODE                           ***********
// let playerRed = "R";
let playerBlue = 'B';
let playerYellow = 'Y';
let currPlayer = null; //= playerYellow

const handle_gescand = function (json) {
  if (json == 'geel') {
    currPlayer = playerYellow;
  } else if (json == 'blauw') {
    // currPlayer = playerRed

    currPlayer = playerBlue;
  }
};

let gameOver = false;
let board;

let rows = 6;
let columns = 7;
let currColumns = []; //keeps track of which row each column is at.

function setGame() {
  board = [];
  currColumns = [5, 5, 5, 5, 5, 5, 5]; //begin van de kolommen

  for (let r = 0; r < rows; r++) {
    //r voor rows
    let row = []; //rij creeren
    for (let c = 0; c < columns; c++) {
      //c voor collumns
      // JS
      row.push(' '); //white space
      // HTML
      //<div id="0-0" class="tile"></div>
      let tile = document.createElement('div'); // 1 gokje van de 4 op een rij wordt div gemaakt
      tile.id = r.toString() + '-' + c.toString(); //id = rijnummer-collnummer om te communiceren met js
      tile.classList.add('tile'); //klasse tile voor later te stylen
      tile.addEventListener('click', setPiece); //als er geklikt wordt stuk insteken
      document.getElementById('board').append(tile); //we voegen de gemaakte div toe aan aan id board
    }
    board.push(row); //we voegen het toe aan ons js bord
  }
}

function verwijderPiece() {
  if (laatstGezetteTile != null) {
    laatstGezetteTile.classList.remove('blue-piece');
    laatstGezetteTile.classList.remove('yellow-piece');
    r += 1; //update the row height for that column start bij het laagste
    currColumns[c] = r; //update the array
    socket.emit('F2B_geslaagd_true');
  }
}

function setPiece() {
  if (gameOver) {
    return; //als er een winner is doe niets
  }

  //get coords of that tile clicked
  // let coords = this.id.split("-"); //van 0-0 naar ["0","0"]
  // let r = parseInt(coords[0]); //hier halen we de rij en de kolom uit
  // let c = parseInt(coords[1]);

  // figure out which row the current column should be on
  r = currColumns[c];

  if (r < 0) {
    // board[r][c] != ' '
    return;
  }

  board[r][c] = currPlayer; //update JS board
  let tile = document.getElementById(r.toString() + '-' + c.toString());
  laatstGezetteTile = tile;
  if (currPlayer == playerBlue) {
    // tile.classList.add("red-piece"); //nu zetten we een stuk op de locatie waar we klikken
    tile.classList.add('blue-piece'); //nu zetten we een stuk op de locatie waar we klikken
    // currPlayer = playerYellow; //zorgt ervoor dat het telkens wisselt
  } else {
    tile.classList.add('yellow-piece');
    // currPlayer = playerRed;
  }

  r -= 1; //update the row height for that column start bij het laagste
  currColumns[c] = r; //update the array

  checkWinner();
}

function checkWinner() {
  // horizontal
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < columns - 3; c++) {
      if (board[r][c] != ' ') {
        if (board[r][c] == board[r][c + 1] && board[r][c + 1] == board[r][c + 2] && board[r][c + 2] == board[r][c + 3]) {
          setWinner(r, c);
          return;
        }
      }
    }
  }

  // vertical
  for (let c = 0; c < columns; c++) {
    for (let r = 0; r < rows - 3; r++) {
      if (board[r][c] != ' ') {
        if (board[r][c] == board[r + 1][c] && board[r + 1][c] == board[r + 2][c] && board[r + 2][c] == board[r + 3][c]) {
          setWinner(r, c);
          return;
        }
      }
    }
  }

  // anti diagonal
  for (let r = 0; r < rows - 3; r++) {
    for (let c = 0; c < columns - 3; c++) {
      if (board[r][c] != ' ') {
        if (board[r][c] == board[r + 1][c + 1] && board[r + 1][c + 1] == board[r + 2][c + 2] && board[r + 2][c + 2] == board[r + 3][c + 3]) {
          setWinner(r, c);
          return;
        }
      }
    }
  }

  // diagonal
  for (let r = 3; r < rows; r++) {
    for (let c = 0; c < columns - 3; c++) {
      if (board[r][c] != ' ') {
        if (board[r][c] == board[r - 1][c + 1] && board[r - 1][c + 1] == board[r - 2][c + 2] && board[r - 2][c + 2] == board[r - 3][c + 3]) {
          setWinner(r, c);
          return;
        }
      }
    }
  }
}

function setWinner(r, c) {
  let winner = document.getElementById('winner');
  let htmlString = '';
  if (board[r][c] == playerBlue) {
    openWinner();
    htmlString = 'Blauw wint';
  } else {
    openWinner();
    htmlString = 'Geel wint';
  }
  winner.innerHTML = htmlString;
  gameOver = true;
}

//#endregion

function openGeel() {
  document.getElementById('opdracht-geel').style.display = 'block';
}

function openBlauw() {
  document.getElementById('opdracht-blauw').style.display = 'block';
}

function closeGeslaagd() {
  document.getElementById('mygeslaagd').style.display = 'none';
}

function openGeslaagd() {
  document.getElementById('mygeslaagd').style.display = 'block';
}

function closeOpdracht() {
  document.getElementById('myopdracht').style.display = 'none';
  socket.emit('F2B_opdracht_geel_minuten', aantal_minuten_geel);
  socket.emit('F2B_opdracht_blauw_minuten', aantal_minuten_blauw);
  aantal_minuten_blauw = 0;
  aantal_minuten_geel = 0;
}

function openOpdracht() {
  document.getElementById('myopdracht').style.display = 'block';
}

function openWinner() {
  document.getElementById('mywinner').style.display = 'block';
  newGame();
}

function closeWinner() {
  document.getElementById('mywinner').style.display = 'none';
}

function openWater() {
  document.getElementById('mywater').style.display = 'grid';
}

function closeWater() {
  document.getElementById('mywater').style.display = 'none';
}

function openCold() {
  document.getElementById('mycold').style.display = 'grid';
}

function closeCold() {
  document.getElementById('mycold').style.display = 'none';
}

function openBadges() {
  closeGespeelde();
  closeTemp();
  document.getElementById('myhistoriek').style.display = 'block';
}

function closeBadges() {
  document.getElementById('myhistoriek').style.display = 'none';
}
function openTemp() {
  closeGespeelde();
  closeBadges();
  document.getElementById('mygrafiek').style.display = 'block';
}

function closeTemp() {
  document.getElementById('mygrafiek').style.display = 'none';
}

function openGespeelde() {
  closeTemp();
  closeBadges();
  document.getElementById('mygespeelde').style.display = 'block';
}

function closeGespeelde() {
  document.getElementById('mygespeelde').style.display = 'none';
}

function openGeelGespeeld() {
  document.getElementById('gespeeldgeel').style.display = 'grid';
}

function openBlauwGespeeld() {
  document.getElementById('gespeeldblauw').style.display = 'grid';
}

const beginner = function () {
  socket.emit('F2B_beginner');
};

//#region ***  Init / DOMContentLoaded                  ***********
document.addEventListener('DOMContentLoaded', function () {
  console.info('DOM geladen');

  const getGrafiek = function () {
    handleData(`http://${lanIP}/api/v1/grafiek/`, showGrafiek);
  };

  const showGrafiek = function (jsonObject) {
    for (const temp of jsonObject.temp) {
      grafiekData.push(parseFloat(temp.waarde));
      grafiekLabel.push(temp.tijdstip);
    }
    console.log(grafiekData);
    console.log(grafiekLabel);
    const ctx = document.getElementById('myChart').getContext('2d');
    const myChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: grafiekLabel,
        datasets: [
          {
            label: 'Temperatuur in graden Celcius',
            data: grafiekData,
            backgroundColor: ['rgba(255, 99, 132, 0.2)'],
            borderColor: ['rgba(255, 99, 132, 1)'],
            borderWidth: 1,
          },
        ],
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  };

  //#region ***  Grafiek content                 ***********

  //#endregion

  htmlHistoriek = document.querySelector('.historiek');
  htmlIndex = document.querySelector('.html-index');
  htmlOpdracht = document.querySelector('.js-opdracht');
  htmlOpdrachtGeel = document.querySelector('.js-opdracht-geel');
  htmlOpdrachtBlauw = document.querySelector('.js-opdracht-blauw');
  htmlBeginner = document.querySelector('.html-beginner');
  htmlGespeeldGeel = document.querySelector('.gespeeldgeel');
  htmlGespeeldBlauw = document.querySelector('.gespeeldblauw');
  htmlProcent = document.querySelector('.procentueel');

  // listenToUI();
  if (htmlIndex) {
    setGame();
    gescand();
    listenToSocketGame();
    listenToSocketTemp();
  }

  listenToSocket();

  if (htmlHistoriek) {
    getHistoriek();
    getGrafiek();
    getGespeeldBlauw();
    getGespeeldGeel();
    getAantalBlauw();
    getAantalGeel();
  }

  if (htmlBeginner) {
    beginner();
  }
});
//#endregion
