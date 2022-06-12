const lanIP = `${window.location.hostname}:5000`;
console.log(lanIP);

const nieuweActiviteit = function () {
  let form = document.querySelector('#activiteitForm');
  console.log(form);
  let formdata = new FormData(form);

  activiteit = formdata.get('activiteit');
  isWater = formdata.get('isWater');
  aantalMinuten = formdata.get('aantalMinuten');

  if (activiteit && isWater && aantalMinuten) {
    const jsonObject = JSON.stringify({ activiteit: activiteit, isWater: isWater, aantalMinuten: aantalMinuten });
    handleData(`http://${lanIP}/api/v1/activiteiten/`, callback, callbackError, (method = 'POST'), jsonObject);
  } else {
    toonError('Niet alle gegevens zijn ingevuld');
  }
};
const callback = function () {
  let succes = document.querySelector('.succes');
  succes.classList.remove('hidden');
  succes.innerHTML = 'Activiteit toevoegen is gelukt!';
  document.querySelector('#activiteitForm').reset();

  setTimeout(function () {
    succes.classList.add('hidden');
    succes.innerHTML = '';
  }, 5000);
};
const callbackError = function (error) {
  toonError(error);
};

const toonError = function (errorTekst) {
  let error = document.querySelector('.error');
  console.log(error);
  error.classList.remove('hidden');
  error.innerHTML = errorTekst;

  setTimeout(function () {
    error.classList.add('hidden');
    error.innerHTML = '';
  }, 5000);
};
