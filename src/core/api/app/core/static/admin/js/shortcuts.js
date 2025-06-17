document.addEventListener('DOMContentLoaded', () => {
    const links = JSON.parse(document.getElementById('shortcuts-links').textContent);
    let visible = false;
    const back = document.createElement('div');
    back.setAttribute('id', 'shortcuts');
    back.setAttribute('tabindex', '');
    const select = document.createElement('select');
    const empty = document.createElement('option');
    select.appendChild(empty);
    links.forEach(({name, url}) => {
      const option = document.createElement('option');
      option.setAttribute('value', url);
      option.innerText = name;
      select.appendChild(option);
    });
  
    back.appendChild(select);
    document.querySelector('body').appendChild(back);
  
    const show = () => {
      visible = true;
      back.style.display = 'block';
      $(select).val(null).trigger('change').select2('open');
    };
  
    const hide = () => {
      visible = false;
      $(select).select2('close');
      back.style.display = 'none';
    };
  
    const toggle = () => {
      visible ? hide() : show();
    };
  
    const backKeyDown = (event) => {
      if (event.keyCode === 27) {
        hide();
      }
    };
  
    const backClick = (event) => {
      hide();
    };
  
    const documentKeyDown = (event) => {
      if (event.keyCode === 75 && (event.ctrlKey || event.metaKey)) {
        toggle();
        event.preventDefault();
      }
    };
  
    const selectSelect = (event) => {
      hide();
      window.location.href = event.params.data.id;
    };
  
    const selectClose = (event) => {
      hide();
    };
  
    const selectOpen = (event) => {
      document.querySelector('.select2-container--open .select2-search__field').focus()
    };
  
    back.addEventListener('keydown', backKeyDown);
    back.addEventListener('click', backClick);
    document.addEventListener('keydown', documentKeyDown);
    $(select).on('select2:select', selectSelect);
    $(select).on('select2:close', selectClose);
    $(select).on('select2:open', selectOpen);
  
    $(document).ready(function() {
      $(select).select2({
        allowClear: true,
        placeholder: 'Shortcuts...',
      });
    });
  
    window.toggleShortcuts = toggle;
  }, false);
  