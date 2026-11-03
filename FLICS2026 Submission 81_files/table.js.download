// EasyChair source script
// (c) 2010-2016 easychair.org
// (c) 2018-2019,2023,2025 EasyChair Ltd

"use strict";

/** @typedef {{head?: HTMLElement, rows: HTMLElement[]}} Section */

function Tab(id,uniqueId,hasHeader,hasSummary,hashScroll)
{
  try {
    this.id = id;
    /** Instead of array with rows we use array with sections. Every
     * section is an array with rows.
     * @type {Section[]} */
    this.sections = [];
    this.numberOfRows = 0;
    Tab.tables[id] = this;
    this.navigation = false; // if true, has navigation bar
    // this is the table state
    this.inc = false; // if true, then sorting in an increasing order
    this.currentColumn = -1; // current sort column
    this.page = 1;
    this.displayRows = 50;
    this.search = '';
    this.drawing = false;
    this.uniqueId = uniqueId;
    this.hasHeader = hasHeader;
    this.hasSummary = hasSummary;
    this.hashScroll = hashScroll;
  }
  catch (err) {
    logError(err,'Tab.new');
  }
} // Tab

Tab.tables = {};

Tab.init = function(element)
{
  try {
    var tables = [];
    // In the case of the initial loading of the page we have to check
    // Tab.tables because perl can add it via <script> and these tables
    // will not be found by findTables()
    if (element === document) {
      tables.push(...values(Tab.tables));
    }
    tables.push(...Tab.findTables(element));
    var iter = tables.iterator();
    var hashScroll = false;
    while (iter.hasNext()) {
      var tab = iter.next();
      tab.initialize();
      tab.restoreState();
      hashScroll = hashScroll || tab.hashScroll;
    }

    // add eventLintener only once on the initial loading
    if (element === document && hashScroll) {
      addEventHandler(window, 'hashchange', Tab.hashChanged);
      // scroll element into view if the page hash contains an element name
      Tab.hashChanged2(location.hash);
    }
  }
  catch (err) {
    logError(err,'Tab.init');
  }
} // Tab.init

/**
 * Find all new kind tables on the page and process it.
 * @param {HTMLElement} element - The base element from need to start searching
 */
Tab.findTables = function (element) {
  try {
    var result = [];
    var allTables = element.getElementsByTagName('table');
    for (var t = 0; t < allTables.length; ++t) {
      var table = allTables[t];
      var dataset = table.dataset;
      if (dataset.kind === 'new') {
        var id = table.id;
        var uid = dataset.uid;
        var hasHeader = dataset.header === 'true';
        var hasSummary = dataset.summary === 'true';
        var hashScroll = dataset.scroll === 'true';

        var sort = {};
        var headersColumn = table.getElementsByTagName('th');
        var header = null;
        // need to find the header with sort columns.
        for (var i = 0; i < headersColumn.length; ++i) {
          var cell = headersColumn[i];
          if (cell.dataset.sort) {
            header = cell.parentElement;
            break;
          }
        }

        // add listeners to found header
        if (header) {
          for (var i = 0; i < header.children.length; ++i) {
            var column = header.children[i];
            var sortKind = column.dataset.sort;
            if (sortKind) {
              sort[i + 1] = sortKind;
              column.addEventListener('click', Tab.sortColumn.bind(null, id, i + 1));
            }
          }
        }

        var tab = new Tab(id, uid, hasHeader, hasSummary, hashScroll);
        tab.setSort(sort);
        result.push(tab);
      }
    }
    return result;
  } catch (err) {
    logError(err, 'Tab.findTables');
  }
} // findTables

Tab.saveAll = function()
{
  try {
    var iter = values(Tab.tables).iterator();
    while (iter.hasNext()) {
      iter.next().saveState();
    }
  }
  catch (err) {
    logError(err,'Tab.saveAll');
  }
} // Tab.saveAll

Tab.sortColumn = function(tableId,columnNumber)
{
  try {
    if (!pageLoaded) {
      Tab.notFullyLoaded();
      return;
    }
    Tab.tables[tableId].sortOn(columnNumber);
  }
  catch (err) {
    logError(err,'Tab.sortColumn');
  }
} // Tab.sortColumn

Tab.notFullyLoaded = function()
{
  alert('It seems that the table was not fully loaded, so this operation cannot be performed.');
} // Tab.notFullyLoaded

Tab.prototype = {
  initialize : function()
  {
    try {
      var tab = $(this.id);
      /** @type {HTMLCollection} */
      var rows = tab.rows;
      if (!rows) { // browser bugs???
        return;
      }

      var entriesField = $(this.id + ':entries');
      if (entriesField) {
        this.displayRows = EC.getSelection(entriesField);
        if (this.displayRows !== 'all') {
          this.displayRows = Number(this.displayRows);
        }
        this.navigation = true;
      }

      // add attributes for the primary sort
      var startRow = this.navigation ? 1 : 0;
      if (this.hasHeader) {
        startRow++;
      }
      var endRow = rows.length;
      if (this.hasSummary) {
        endRow--;
      }
      /** @type {Section} */
      var section = {
        rows: []
      };
      for (var n = startRow; n < endRow; n++) {
        var row = rows[n];
        addDebug('init_n',n);
        addDebug('init_r',row ? 1 : 0);
        if (row.dataset.ignore) {
          if (section.head || section.rows.length) {
            this.sections.push(section);
            section = {
              rows: []
            };
          }
          section.head = row;
          continue;
        }
        section.rows.push(row);
        this.numberOfRows++;

        row['ec:prim'] = this.navigation ? n - 1 : n;

        var cells = row.cells;
        for (var c = cells.length - 1; c >= 0; c--) {
          var cell = cells[c];
          // innerText works too long if we will do it every time, so we store
          // the content of the cell
          cell['ec:content'] = cell.innerText;
        }
      }
      if (section.head || section.rows.length) {
        this.sections.push(section);
      }
      this.redraw();
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.initialize');
    }
  }, // initialize

  dumpDebug : function()
  {
    try {
      addDebug('tableId',this.id);
      addDebug('numberOfRows',this.numberOfRows);
      addDebug('navigation',this.navigation);
      addDebug('hasHeader',this.hasHeader);
      addDebug('hasSummary',this.hasSummary);
      addDebug('inc',this.inc);
      addDebug('currentColumn',this.currentColumn);
      addDebug('page',this.page);
      addDebug('displayRows',this.displayRows);
      addDebug('search',this.search);
      addDebug('drawing',this.drawing);
      addDebug('uniqueId',this.uniqueId);
    }
    catch (err) {
      logError(err,'Tab.dumpDebug');
    }
  }, // dumpDebug

  setSort : function(sort)
  {
    this.sort = sort;
  },

  /**
   * Returns a table cell that need to compare for the currentColumn according
   * colspan in the row.
   * @param {HTMLTableRowElement} row - Table row for comparign.
   * @returns {HTMLTableCellElement}
   */
  getComparableCell: function(row) {
    var index = -1;
    var column = this.currentColumn;
    while (column > 0) {
      index++;
      column -= row.cells[index].colSpan;
    }
    return row.cells[index];
  }, // getComparableCell

  /**
   * Returns the index of the find row. If there are no this row, returns -1.
   * @param {HTMLTableRowElement} row - Row in the table that need to find index.
   * @returns {number}
   */
  getRowIndex: function(row) {
    var index = 0;
    for (var k = 0; k < this.sections.length; ++k) {
      var section = this.sections[k];
      for (var l = 0; l < section.rows.length; ++l) {
        if (section.rows[l] === row) {
          return index;
        }
        index++;
      }
    }
    return -1;
  },

  cellCompare: function(row1, row2)
  {
    try {
      var result = 0;
      var currentColumn = this.currentColumn;
      var sortKind = this.sort[currentColumn];
      var prim1 = row1['ec:prim'];
      if (!prim1) {
        return -1;
      }
      var prim2 = row2['ec:prim'];
      if (!prim2) {
        return 1;
      }

      var key1;
      var key2;
      if (sortKind === 'primary') {
        key1 = prim1;
        key2 = prim2;
      }
      else {
        var cell1 = this.getComparableCell(row1);
        var cell2 = this.getComparableCell(row2);
        var text1 = cell1.dataset.key || cell1['ec:content'];
        var text2 = cell2.dataset.key || cell2['ec:content'];
        switch (sortKind) {
          case 'bool':
            key1 = Boolean(text1);
            key2 = Boolean(text2);
            break;
          case 'int':
            key1 = parseInt(text1);
            key1 = isNaN(key1) ? -Infinity : key1;
            key2 = parseInt(text2);
            key2 = isNaN(key2) ? -Infinity : key2;
            break;
          case 'float':
          case 'number':
            key1 = parseFloat(text1);
            key1 = isNaN(key1) ? -Infinity : key1;
            key2 = parseFloat(text2);
            key2 = isNaN(key2) ? -Infinity : key2;
            break;
          case 'string':
            key1 = text1;
            key2 = text2;
            break;
          default:
            throw new Error('Incorrect sortKind');
            break;
        }
      }

      if (key1 < key2) {
        result = -1;
      }
      else if (key1 > key2) {
        result = 1;
      }
      else if (prim1 < prim2) {
        return -1;
      }
      else if (prim2 < prim1) {
        return 1;
      }
      else {
        return 0;
      }

      return this.inc ? result : -result;
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.cellCompare');
    }
  }, // cellCompare

  sortOn : function(column)
  {
    try {
      if (this.drawing) {
        return;
      }
      this.drawing = true;
      this.page = 1;
      var tab = $(this.id);
      var rows = tab.rows;
      var headerRowIndex = this.navigation ? 1 : 0;
      var header = rows[headerRowIndex];
      if (this.currentColumn == column) {
        this.inc = ! this.inc;
      }
      else {
        var lastRowIndex = rows.length - 1;
        if (this.hasSummary) {
          lastRowIndex--;
        }
        if (this.currentColumn != -1) {
          header.cells[this.currentColumn-1].className = 'sort_both';
          for (var i = 0; i < this.sections.length; ++i) {
            for (var j = 0; j < this.sections[i].rows.length; ++j) {
              removeClass(this.getComparableCell(this.sections[i].rows[j]),
                'high');
            }
          }
        }
        this.inc = false;
        this.currentColumn = column;
        for (var i = 0; i < this.sections.length; ++i) {
          for (var j = 0; j < this.sections[i].rows.length; ++j) {
            addClass(this.getComparableCell(this.sections[i].rows[j]), 'high');
          }
        }
      }
      header.cells[column-1].className = this.inc ? 'sort_asc' : 'sort_desc';
      var myself = this;
      for (var i = 0; i < this.sections.length; ++i) {
        var sectionRows = this.sections[i].rows;
        if (sectionRows.length === 0) { // empty section
          continue;
        }
        sectionRows.sort(function(cellA, cellB) {
          return myself.cellCompare(cellA, cellB);
        });
        var tableSection = sectionRows[0].parentNode;
        for (var n = sectionRows.length - 2; n >= 0; n--) {
          var row1 = sectionRows[n];
          var row2 = sectionRows[n + 1];
          if (row1 && row2) { // added 23/07/2012 to prevent errors for pages incompletely loaded
            tableSection.insertBefore(row1,row2);
          }
        }
      }
      this.redraw();
      this.drawing = false;
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.sortOn');
    }
  }, // sortOn

  /**
   * Show the header if it exists for all sections from array.
   * @param {Section[]} sections - Sections that need to show the header.
   */
  showSectionsHeader: function(sections) {
    for (var i = 0; i < sections.length; ++i) {
      if (sections[i].head) {
        removeClass(sections[i].head, 'hidden');
      }
    }
  }, // showSectionsHeader

  // Redraw the table depending on the current state. This function assumes
  // the rows are already sorted and simply checks which rows should be hidden
  redraw : function()
  {
    try {
      if (!this.navigation) {
        return;
      }
      // the page should display eligible entries between first and last, counting from 1
      var displayAll = this.displayRows == 'all';
      var last = displayAll ? this.numberOfRows : this.page * this.displayRows;
      var first = displayAll ? 1 : last - this.displayRows + 1;
      var eligible = 0;
      /** Section without eligible elements.
       * @type {Section[]}
       */
      var noEligibleElements = [];
      /* Logic of showing section headers:
         We should show all section headers from the first section that have
         visible elements to the last section that have visible elements.
         There may be sections between the first and the last without
         visible/eligible rows, we also should show it.
         Plus all section headers before the first without eligible rows.
         Plus all section headers after the last section if this is the last
         page. */
      for (var i = 0; i < this.sections.length; ++i) {
        var section = this.sections[i];
        var hasEligibleElements = false;
        var hasVisibleElements = false;
        var firstEligibleElementIsVisible = false;
        if (section.head) {
          addClass(section.head, 'hidden');
        }
        for (var j = 0; j < section.rows.length; ++j) {
          var row = section.rows[j];

          if (this.search && !Tab.matchRow(row, this.search)) {
            addClass(row, 'hidden');
            continue;
          }

          eligible++;
          if (eligible >= first && eligible <= last) {
            removeClass(row, 'hidden');
            hasVisibleElements = true;
            if (!hasEligibleElements) {
              firstEligibleElementIsVisible = true;
            }
          } else {
            addClass(row,'hidden');
          }
          hasEligibleElements = true;
        }
        if (hasVisibleElements && section.head) {
          removeClass(section.head, 'hidden');
        }
        if (hasEligibleElements) {
          if (firstEligibleElementIsVisible) {
            this.showSectionsHeader(noEligibleElements);
          }
          noEligibleElements = [];
        } else {
          noEligibleElements.push(section);
        }
      }
      // Or displayAll is true, or it is last page.
      if (displayAll || this.page === Math.ceil(eligible / this.displayRows)) {
        this.showSectionsHeader(noEligibleElements);
      }

      // change the "showing n entries" part of the bar
      $(this.id + ':rows').innerHTML = eligible;
      $(this.id + ':from').innerHTML = eligible < first ? 0 : first;
      $(this.id + ':to').innerHTML = eligible < first ? 0 : eligible < last ? eligible : last;
      // change the pages bar
      $(this.id + ':previous').style.visibility = this.page > 1 ? 'visible' : 'hidden';
      $(this.id + ':next').style.visibility = eligible > last ? 'visible' : 'hidden';

      var rightLinks = displayAll ? 0 : Math.ceil((eligible - last) / this.displayRows);
      var leftLinks = displayAll ? 0 : ((first - 1) / this.displayRows);
      if (leftLinks + rightLinks > 8) {
        if (leftLinks > 4) {
          if (rightLinks >= 4) {
            leftLinks = 4;
          }
          else {
            leftLinks = 8 - rightLinks;
          }
        }
        if (rightLinks > 4) {
          if (leftLinks >= 4) {
            rightLinks = 4;
          }
          else {
            rightLinks = 8 - leftLinks;
          }
        }
      }
      var allHidden = displayAll || (first == 1 && eligible <= last);
      var slices = Math.ceil(this.numberOfRows / 10);
      var fromSlice = this.page - leftLinks;
      var toSlice = this.page + rightLinks;
      for (var n = slices; n > 0; n--) {
        var selected = $(this.id + ':sel' + n);
        var pageLink = $(this.id + ':page' + n);
        if (allHidden || n < fromSlice || n > toSlice) {
          addClass(selected,'hidden');
          addClass(pageLink,'hidden');
        }
        else if (n == this.page) {
          removeClass(selected,'hidden');
          addClass(pageLink,'hidden');
        }
        else {
          addClass(selected,'hidden');
          removeClass(pageLink,'hidden');
        }
      }
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.redraw');
    }
  }, // redraw

  // function called when the user changes the number of displayed entries
  changeEntries : function()
  {
    try {
      if (!pageLoaded) {
        Tab.notFullyLoaded();
        return;
      }
      var field = $(this.id + ':entries');
      if (this.drawing) {
        EC.setSelection(field,this.displayRows);
        return;
      }
      this.drawing = true;
      this.page = 1;
      this.displayRows = EC.getSelection(field);
      this.redraw();
      this.drawing = false;
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.changeEntries');
    }
  }, // changeEntries

  // function called when the user clicks on "next page"
  nextPage : function()
  {
    try {
      return this.setPage(this.page+1);
    }
    catch (err) {
      logError(err,'Tab.nextPage');
    }
  }, // nextPage

  // function called when the user clicks on "previous page"
  previousPage : function()
  {
    try {
      return this.setPage(this.page-1);
    }
    catch (err) {
      logError(err,'Tab.previousPage');
    }
  }, // previousPage

  // function called when the user clicks on a page number
  // page numbers start from 1
  setPage : function(page)
  {
    try {
      if (!pageLoaded) {
        Tab.notFullyLoaded();
        return;
      }
      if (this.drawing) {
        return false;
      }
      this.drawing = true;
      this.page = page;
      this.redraw();
      this.drawing = false;
      return false;
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.setPage');
    }
  }, // setPage

  searchUpdate : function()
  {
    try {
      if (!pageLoaded) {
        Tab.notFullyLoaded();
        return;
      }
      var searchString = $(this.id + ':search').value;
      if (searchString == this.search) {
        return;
      }
      if (this.drawing) {
        // there should be rescheduling of this function call in future
        return;
      }
      this.search = searchString;
      this.drawing = true;
      this.page = 1;
      this.redraw();
      this.drawing = false;
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.searchUpdate');
    }
  }, // searchUpdate

  // save state in the session storage
  saveState : function()
  {
    try {
      saveObject(this.uniqueId,
                 {i : this.inc,c : this.currentColumn,p : this.page,
                  d : this.displayRows,s : this.search});
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.saveState');
    }
  },

  // restore state from the session storage
  restoreState : function()
  {
    try {
      var uniqueId = this.uniqueId;
      var state = getObject(uniqueId);
      if (!state) {
        return;
      }
      this.displayRows = state.d;
      if (this.navigation) {
        EC.setSelection($(this.id + ':entries'),state.d);
        this.search = state.s;
        $(this.id + ':search').value = state.s;
      }
      if (state.c != -1) {
        this.sortOn(state.c);
        // if the order is reverse, it should be sorted twice
        if (state.i) {
          this.sortOn(state.c);
        }
      }
      this.page = state.p;
      this.redraw();
      deleteObject(this.uniqueId);
    }
    catch (err) {
      this.dumpDebug();
      logError(err,'Tab.restoreState');
    }
  }
}; // Tab.prototype

Tab.matchRow = function(row,searchString)
{
  try {
    searchString = searchString.toLowerCase();
    var cells = row.cells;
    for (var c = cells.length - 1; c >= 0; c--) {
      if (cells[c]['ec:content'].toLowerCase().trim().indexOf(searchString) !== -1) {
        return true;
      }
    }
    return false;
  }
  catch (err) {
    logError(err,'Tab.matchRow');
  }
} // Tab.matchRow

Tab.hashChanged = function(event)
{
  try {
    Tab.hashChanged2(event.newURL);
  }
  catch (err) {
    logError(err,'Tab.hashChanged');
  }
} // Tab.hashChanged

Tab.hashChanged2 = function(URL)
{
  try {
    var hashIndex = URL.indexOf('#');
    if (hashIndex == -1) {
      return;
    }
    var name = URL.substring(hashIndex + 1);
    if (name == '') {
      return;
    }

    // find if the element with this name is contained in a table row
    var elements = document.getElementsByName(name);
    for (var i = 0; i < elements.length; ++i) {
      var tableRow = elements[i];
      while (tableRow && tableRow.tagName != 'TR') {
        tableRow = tableRow.parentNode;
      }
      if (!tableRow) {
        continue;
      }
      // tableRow is a <tr> element
      // find a <table> element containing this row
      var table = tableRow.parentNode;
      while (table.tagName != 'TABLE') {
        table = table.parentNode;
      }
      var tab = Tab.tables[table.id];
      if (!tab) { // table element but not one of our tables
        continue;
      }
      if (!tab.hashScroll) {
        // tab found but we should not scroll to it
        return;
      }

      if (tab.search) {
        $(tab.id + ':search').value = '';
        tab.search = '';
      }

      var page = 1;
      var rowsCount = parseInt(tab.displayRows);
      if (rowsCount) {
        var index = tab.getRowIndex(tableRow);
        page = Math.floor(index / rowsCount) + 1;
      }
      tab.setPage(page);
      tableRow.scrollIntoView();
      return;
    }
  }
  catch (err) {
    logError(err,'Tab.hashChanged2');
  }
} // Tab.hashChanged2

onLoad.on(Tab.init);
addOnBeforeUnload(Tab.saveAll);
