// EasyChair source file
// (c) 2020 EasyChair Ltd

"use strict";

var Menu = {
  selected: null, // id of the tab under cursor
  parent: {}, // the parent relation
  hideTime: 25, // time after which menu is hidden onmouseout
  timeout: -1,
  high: {}, // all highlighted tabs

  followLink: function(id, url) {
    try {
      Menu.selected = null,
      Menu.hideAll();
      location.href = url;
    } catch (err) {
      logError(err, 'Menu.followLink');
    }
  },

  followLink2: function(id, url, pars) {
    try {
      Menu.selected = null,
      Menu.hideAll();
      location.href = href(url, pars);
    } catch (err) {
      logError(err, 'Menu.followLink');
    }
  },

  // hide menu after time interval md
  hide: function(id) {
    try {
      if (Menu.selected == id) {
        Menu.selected = null;
      }
      Menu.timeout = setTimeout('Menu.hideAll()', Menu.hideTime);
    }
    catch (err) {
      logError(err, 'Menu.hide');
    }
  },

  // for a menu tab with a given id, return the set of all its ancestor tabs
  ancestors: function(id) {
    var result = {};
    result[id] = true;
    var el = $(id).parentNode;
    while (el) {
      if (! el.id || el.id.substring(0, 5) !== 'tmenu') {
        el = el.parentNode;
        continue;
      }
      var parentId = el.id.substring(1);
      result[parentId] = true;
      el = $(parentId).parentNode;
    }
    return result;
  },

  // unhighlight all highlighted tabs not inherited from
  // the selected element and hide their menus
  hideAll: function(){
    try {
      var shown = Menu.selected ? Menu.ancestors(Menu.selected) : {};
      for (var id in Menu.high) {
        if (shown[id]) continue;

        delete Menu.high[id];
        var menuTab = $(id);
        // this happens with incomplete pages (browser bugs?)
        if (!menuTab) return;

        var st = menuTab.style;
        // also happens with incomplete pages
        if (!st) return;

        var menu = $('t' + id);
        if (menu) {
          menu.style.visibility = 'hidden';
        }
      }
    }
    catch (err) {
      logError(err, 'Menu.hideAll');
    }
  },

  // show menu with a given index
  show: function(id) {
    try {
      // browser bug
      if (!id || id == Menu.selected) return;

      Menu.selected = id;
      Menu.high[id] = true;
      var tab = $(id);
      // happens due to browser bugs
      if (!tab || !tab.style) return;

      var submenu = $('t' + id);
      if (submenu) {
        var pos = absPosition(tab);
        if (tab.className == 'top') {
          submenu.style.top = (pos.bottom - 2) + 'px';
          submenu.style.left = (pos.left + 2) + 'px';
        }
        else {
          submenu.style.top = (pos.top + 1) + 'px';
          submenu.style.left = (pos.right - 9) + 'px';
        }

        // return submenu to the screen if it tries to go outside
        var windowWidth = document.documentElement.clientWidth;
        var submenuBox = submenu.getBoundingClientRect();
        if (submenuBox.right > windowWidth) {
          var newLeft;
          if (tab.className == 'top') {
            newLeft = windowWidth - submenuBox.width + window.pageXOffset;
          } else {
            var tabBox = tab.getBoundingClientRect();
            newLeft = pos.right + 9 - submenuBox.width - tabBox.width;
          }
          if (newLeft - window.pageXOffset >= 0) {
            // we have to change position only if the user has more or less
            // big screen, otherwise it is useless
            submenu.style.left = newLeft + 'px';
          }
        }

        submenu.style.visibility = 'visible';
      }
      Menu.hideAll();
    }
    catch (err) {
      logError(err, 'Menu.show');
    }
  }
};
