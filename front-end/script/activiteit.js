const nieuweActiviteit = function () {
  let form = document.querySelector('#activiteitForm');
  console.log(form);
  let formdata = new FormData(form);
  console.log(formdata.get('activiteit'));
};
