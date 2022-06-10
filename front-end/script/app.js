'use strict';
const lanIP = `${window.location.hostname}:5000`;
console.log(lanIP);
const socket = io(`http://${lanIP}`);

//#region ***  DOM references                           ***********
let htmlHistoriek, htmlIndex, htmlOpdracht;
//#endregion

let huidige_opdracht = '';
let aantal_minuten = 0;
let counterBlauw = 0;
let counterGeel = 0;

//#region ***  4 in a row references                           ***********
let r;
let c;
//#endregion

//#region ***  Callback-Visualisation - show___         ***********
const showHistoriek = function (jsonObject) {
  console.log(jsonObject);
  let htmlString = `<table class="c-table">
      <tr>
        <th>id</th>
        <th>Device</th>
        <th>Tijdstip</th>
        <th>Waarde</th>
      </tr>`;

  for (const historiek of jsonObject.historiek) {
    htmlString += `
          <tr>
            <td>${historiek.idHistoriek}</td>
            <td>${historiek.naam}</td>
            <td>${historiek.tijdstip}</td>
            <td>${historiek.waarde}</td>
          </tr>
        `;
  }
  htmlString += `</table>`;

  htmlHistoriek.innerHTML = htmlString;
};
//#endregion

//#region ***  Data Access - get___                     ***********
const getHistoriek = function () {
  handleData(`http://${lanIP}/api/v1/historiek/`, showHistoriek);
};

//#endregion

//#region ***  functions 4 in a row                     ***********
const positieKolom = function (number) {
  r = 0;
  c = number;
};

// const positieTweedeKolom = function () {
//   r = 0;
//   c = 1;
// };

// const positieDerdeKolom = function () {
//   r = 0;
//   c = 2;
// };

// const positieVierdeKolom = function () {
//   r = 0;
//   c = 3;
// };

// const positieVijfdeKolom = function () {
//   r = 0;
//   c = 4;
// };

// const positieZesdeKolom = function () {
//   r = 0;
//   c = 5;
// };

// const positieZevendeKolom = function () {
//   r = 0;
//   c = 6;
// };

//#endregion

//#region ***  Event Listeners - listenTo___            ***********

const gescand = function () {
  socket.on('B2F_rfid_data', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    handle_gescand(jsonObject);
  });
};

const listenToSocketGame = function () {
  socket.on('B2F_eerste_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
  socket.on('B2F_tweede_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
  socket.on('B2F_derde_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
  socket.on('B2F_vierde_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
  socket.on('B2F_vijfde_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
  socket.on('B2F_zesde_kolom', function (jsonObject) {
    console.log(`Blok in ${jsonObject + 1} kolom`);
    positieKolom(jsonObject);
    setPiece();
  });
  socket.on('B2F_zevende_kolom', function (jsonObject) {
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
};

const listenToSocket = function () {
  socket.on('connected', function () {
    console.log('verbonden met socket webserver');
  });

  socket.on('B2F_opdracht_geel', function (jsonObject) {
    huidige_opdracht = jsonObject.Activiteit;
    console.log(huidige_opdracht);
    aantal_minuten = jsonObject.aantalMinuten;
    socket.emit('F2B_opdracht_geel_minuten', aantal_minuten);
    openOpdracht();
    if (counterGeel == 0) {
      let htmlString = huidige_opdracht;
      htmlOpdracht.innerHTML = htmlString;
    }
  });

  socket.on('B2F_opdracht_blauw', function (jsonObject) {
    huidige_opdracht = jsonObject.Activiteit;
    console.log(huidige_opdracht);
    aantal_minuten = jsonObject.aantalMinuten;
    socket.emit('F2B_opdracht_blauw_minuten', aantal_minuten);
    openOpdracht();
    // if (counterBlauw == 0) {
    let htmlString = huidige_opdracht;
    htmlOpdracht.innerHTML = htmlString;
    // }
  });
};
//#endregion

//#region ***  4 OP EEN RIJ CODE                           ***********
// let playerRed = "R";
let playerBlue = 'B';
let playerYellow = 'Y';
let currPlayer = null; //= playerYellow

const handle_gescand = function (json) {
  if (json == 'geel') {
    counterGeel += 1;
    if (counterGeel == 1) {
      console.log('Team geel opdracht uitvoeren');
    } else if (counterGeel == 2) {
      currPlayer = playerYellow;
      counterGeel = 0;
    }
  } else if (json == 'blauw') {
    // currPlayer = playerRed
    counterBlauw += 1;
    if (counterBlauw == 1) {
      console.log('Team blauw opdracht uitvoeren');
    } else if (counterBlauw == 2) {
      currPlayer = playerBlue;
      counterBlauw = 0;
    }
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
  if (board[r][c] == playerBlue) {
    winner.innerText = 'Blue Wins';
  } else {
    openWinner();
    winner.innerText = 'Yellow Wins';
  }
  gameOver = true;
}

//#endregion

function closeOpdracht() {
  document.getElementById('myopdracht').style.display = 'none';
}

function openOpdracht() {
  document.getElementById('myopdracht').style.display = 'block';
}

function openWinner() {
  document.getElementById('mywinner').style.display = 'block';
}

function closeWinner() {
  document.getElementById('mywinner').style.display = 'none';
}

//#region ***  Init / DOMContentLoaded                  ***********
document.addEventListener('DOMContentLoaded', function () {
  console.info('DOM geladen');

  htmlHistoriek = document.querySelector('.historiek');
  htmlIndex = document.querySelector('.html-index');
  htmlOpdracht = document.querySelector('.js-opdracht');

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
  }
});
//#endregion
