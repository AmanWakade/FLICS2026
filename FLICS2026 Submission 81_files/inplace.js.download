// EasyChair source file
// (c) 2010-2017 Cool Press Ltd
// (c) 2020-2023 EasyChair Ltd

//
// Implements simple in-place editors that can be added to span or div
// elements and also coexist with drag-and-droppable rows
//
// new Inplace(elementId,options)
//   Add an in-place editor to an element with a given id.
//   An Inplace is a hash with the following keys and default values:
//     - clickToEditText: text display when the mouse is over the
//                        element (default "Click to edit") 
//     - okText: text on the OK button (default "save")
//     - cancelText: text on the cancel button (default "cancel")
//     - highlightColor: color of the element when the mouse is over it
//     - onCancel: function of one argument (Inplace) called when the
//       cancel button is pressed. The default behaviour is to hide the
//       editor and restore the text before editing 
//     - confirm: a text given to the confirm() function asking the user before opening the
//                field for editing. Undefined by default
//     - confirm_after: a text given to the confirm() function asking the user before changing
//                      the value. Undefined by default
//     - right: (edit field only) make the edit field right-justified
//     - onOk: function of one argument (Inplace) called when the OK
//             button is pressed. By default: Inplace.standardRequest
//     - size: the length of the input field (default undefined)
//     - rows: the number of rows. If this option is defined then
//             (1) textarea will be used instead of an input field
//             (2) the editor element must be a div element 
//     - cols: the number of columns in the text area or html (default undefined)
//     - kind: one of 'text','date','list','html','color' (default 'text')
//     - values: list of values (for kind='list'). Each value is either a string or an object {val:value,label:label}
//     - value: default value of the inplace field (for kind='date').
//     - selected: the current choice (for kind='list')
//     - ifEmpty: if the current value is empty, then on click this value
//                will be displayed (for 'text', 'date' and 'html' only)
//     - text: the text to edit (for html only)
//  
// Inplace.get(id)
//   Return the inplace editor for an element with a given id
//
// oldText
//   Stores the text before editing or selection for kind='list'
//
// showText(txt)
//   if the element contains an edit field remove it.
//   Set the text of the element to txt
//
// getText()
//   return the edited text 
// getValue()
//   return the selected option value (for kind = 'list')
// reset()
//   remove the input
//
// INTERNALLY
// In addition to the properties set in new() one can use the following
// properties and functions of an Inplace
// 
// element:            the element (div or span) which the editor modifies
// editing:            if true then currently editing
// id:                 the element id
// originalBackground: original background color
// originalCursor:     original cursor
// picker:             the DatePicker object (only if kind='date')
// form:               the form containing all inputs and buttons (when open)
// input:              the text field or area containing the edited text
//                     (for kind='text' and kind='date')
//
// GLOBAL variables:
// Inplace.extra       the hash of parameters that will be added to any loadObject() call
//

function Inplace(id,options)
{
  try {
    var element = $(id);
    if (!element) {
      return;
    }
    if (!element.style) {
      // this happens but very rare when plugins have been installed. Noted with the Skype
      // plugin, for example, but also apsuggestor.com and widgets.maxperview.com
      // there should be a warning for the users that additional scripts break this
      // script
      report('An error was reported. Some add-ons for your browser may make this script not work correctly!',10000);
      return;
    }
    Inplace.addImage(element);
    element.inplace = id;
    this.element = element;
    this.id = element.id;

    this.originalBackground = element.style.backgroundColor;
    this.originalCursor = element.style.cursor;
    // default options
    this.clickToEditText = 'Click to edit';
    this.highlightColor = '#ffff99';
    this.okText = 'Save';
    this.kind = 'text';
    this.cancelText = 'Cancel';
    this.onOk = Inplace.standardRequest;
    Inplace.all[id] = this;
        
    options = options || {};
    for (var opt in options) {
      this[opt] = options[opt];
    }
    if (this.kind == 'list') {
      var vals = this.values;
      for (var i = vals.length-1;i >= 0;i--) {
        var val = vals[i];
        if (typeof val == 'string') {
          vals[i] = {val:val,label:val};
        }
      }
    }
    if (this.kind == 'color') {
      element.style.backgroundColor = '#'+element.innerHTML;
    }
    
    this.setEvents();
  }
  catch (err) {
    logError(err,'inplace.new');
  }
}

Inplace.all = {};

Inplace.prototype = {
  // set all events associated with the element of this editor
  setEvents : function() {
    try {
      var element = this.element;
      element.title = this.clickToEditText;
      element.onmouseover = Inplace.mouseOver;
      element.onmouseout = Inplace.MouseOut;
      element.onclick = Inplace.click;
    }
    catch (err) {
      logError(err,'inplace.setEvents');
    }
  },

  // go to the text mode and display val.
  // text should only be defined for type='html'
  showText : function(val,text,doNotAddImage) {
    try {
      var element = this.element;
      removeChildren(element);
      if (this.kind == 'html') {
        this.text = val;
        element.innerHTML = text || val;
      }
      else if (this.kind == 'color') {
        $T(val,element);
        element.style.backgroundColor = '#'+val;
      }
      else if (this.rows) { // textarea
        var lines = val.split('\n');
        while (lines.length > 1) {
          $T(lines.shift(),element);
          $_('br',{},false,element);
        }
        $T(lines[0],element);
      }
      else {
        $T(val,element);
      }
      Inplace.addImage(element);
      if (this.editing) {
        this.setEvents();
        this.editing = false;
      }
    }
    catch (err) {
      logError(err,'inplace.showText');
    }
  }, // showText

  // the default onCancel function
  onCancel : function() {
    this.showText(this.oldText,this.text,true);
  },

  // if not open yet, created the form with the editor and display it
  open : function()
  {
    try {
      if (this.editing) {
        if (this.input) {
          this.input.focus();
        }
        return;
      }
      // Check if this inplace editor has a confirm message. If yes, run it and
      // if it returns false, do nothing 
      if (this.confirm && !confirm(this.confirm)) {
        return;
      }
      this.editing = true;
      var element = this.element;
      var children = element.childNodes;
      element.removeChild(children[0]);
      // not editing, save the old text or selection
      element.normalize();
      if (this.kind == 'html') {
        this.oldText = element.innerHTML;
      }
      else if (this.rows) {
        this.oldText = elementText(element);
      }
      else {
        this.oldText = element.innerText;
      }
      // remove the previous content
      element.title = '';
      element.style.backgroundColor = this.originalBackground;
      removeChildren(element);
      // add the new content: form with all elements
      var form = $_('form',false,false,element);
      this.form = form;
      var tbl = $_('table',{cellSpacing:0,cellPadding:0,className:'inplace'},false,form);
      var row = tbl.insertRow(0);
      var buttonCell1;
      var buttonCell2;
      if (this.kind == 'date') {
        var value = this.value || this.oldText;
        if (value === '' && this.ifEmpty) {
          value = this.ifEmpty;
        }
        if (! value.match(/^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$/)) { // not in the 'yyyy-mm-dd' format
          value = '';
        }
        var id = this.id;
        this.input = $_('input',
                        {'type':'text',name:'edit',picker:id,id:'ipText'+id,
                         size:'yyyy-mm-dd'.length+1,value:value},
                        false,row.insertCell(0));
        $_('input',
           {'type':'button',value:'',id:'ipButton'+id,
            picker:id,className:'calendar'},
           false,row.insertCell(1));
        buttonCell1 = row.insertCell(2);
        buttonCell2 = row.insertCell(3);
        var pickerOptions = {};
        if (this.min) {
          pickerOptions.minDate = this.min;
        }
        if (this.max) {
          pickerOptions.maxDate = this.max;
        }
        this.picker = new DatePicker('ipText'+id,'ipButton'+id,pickerOptions);
      }
      else if (this.kind == 'list') {
        this.input = $_('select',{},false,row.insertCell(0));
        for (var i = 0;i < this.values.length;i++) {
          var value = this.values[i];
          var label = value.label;
          var val = value.val;
          var opt = $_('option',{value:val},label,this.input);
          if (this.selected) {
            opt.selected = (val == this.selected);
          }
          else {
            opt.selected = (label == this.oldText);
          }
        }
        buttonCell1 = row.insertCell(1);
        buttonCell2 = row.insertCell(2);
      }
      else if (this.kind == 'html') {
        var value = this.text;
        if (value == '') {
          if (this.ifEmpty) {
            value = this.ifEmpty;
          } 
        }
        if (this.rows) {
          var options = {name:'edit',value:value,rows:this.rows};
          if (this.cols) {
            options.cols = this.cols;
          }
          var cell = row.insertCell(0);
          cell.colSpan = 2;
          this.input = $_('textarea',options,false,cell);
          var row1 = tbl.insertRow(1);
          buttonCell1 = row1.insertCell(0);
          buttonCell1.style.width = '1%';
          buttonCell2 = row1.insertCell(1);
          buttonCell2.style.width = '99%';
        }
        else {
          var options = {'type':'text',name:'edit',value:value};
          if (this.size) {
            options.size = this.size;
          }
          else if (value != '') {
            var len = value.length;
            if (len > 18) {
              options.size = len > 78 ? 80 : len+2;
            }
          }
          this.input = $_('input',options,false,row.insertCell(0));
          buttonCell1 = row.insertCell(1);
          buttonCell2 = row.insertCell(2);
        }
      }
      else if (this.kind == 'color') {
        var value = this.oldText;
        if (value == '') {
          if (this.ifEmpty) {
            value = this.ifEmpty;
          } 
        }
        if (! value.match(/^\s*[0-9a-fA-F]{6}\s*$/)) { // not in the 'RRGGBB' format
          value = '';
        }
        var id = this.id;
        this.input = $_('input',
                        {'type':'text',name:'edit',id:'ipText'+id,
                         size:7,value:value},
                        false,row.insertCell(0));
        this.colorPicker = new jscolor.color(document.getElementById('ipText'+id), 
                                             {pickerOnfocus:false, pickerClosable:true})
        var colorPicker = this.colorPicker;
        function openPicker() {
          if (colorPicker.isPickerOwner()) {
            colorPicker.hidePicker()
          }
          else {
            colorPicker.showPicker()
          }
        }
        $_('input',
           {'type':'button',value:'select color',id:'ipButton'+id,
            onclick:openPicker},
           false,row.insertCell(1));
        buttonCell1 = row.insertCell(2);
        buttonCell2 = row.insertCell(3);
      }
      else if (this.rows) { // textarea
        var value = this.oldText;
        if (value == '') {
          if (this.ifEmpty) {
            value = this.ifEmpty;
          } 
        }
        var options = {name:'edit',value:value,rows:this.rows};
        if (this.cols) {
          options.cols = this.cols;
        }
        var cell = row.insertCell(0);
        cell.colSpan = 2;
        this.input = $_('textarea',options,false,cell);
        var row1 = tbl.insertRow(1);
        buttonCell1 = row1.insertCell(0);
        buttonCell1.style.width = '1%';
        buttonCell2 = row1.insertCell(1);
        buttonCell2.style.width = '99%';
      }
      else {
        var value = this.oldText;
        if (value == '') {
          if (this.ifEmpty) {
            value = this.ifEmpty;
          } 
        }
        var options = {'type':'text',name:'edit',value:value};
        if (this.size) {
          options.size = this.size;
        }
        else if (value && value != '') {
          var len = value.length;
          if (len > 18) {
            options.size = len > 78 ? 80 : len+2;
          }
        }
        if (this.right) {
          options.className = 'right';
        }
        this.input = $_('input',options,false,row.insertCell(0));
        buttonCell1 = row.insertCell(1);
        buttonCell2 = row.insertCell(2);
      }

      $_('input',
         {'type':'submit',value:this.okText,onclick : Inplace.defaultOk,className:'save'},
         false,buttonCell1);
      $_('input',{'type':'submit',value:this.cancelText,onclick : Inplace.defaultCancel,className:'cancel'},
         false,buttonCell2);
      element.onmouseover = null;
      element.onmouseout = null;
      element.onclick = null;
      if (this.input) {
        this.input.focus();
      }
    }
    catch (err) {
      logError(err,'inplace.open');
    }
  },

  reset : function()
  {
    try {
      this.editing = false;
      if (this.input) {
        removeElement(this.input);
        this.input = null;
      }
    }
    catch (err) {
      logError(err,'inplace.reset');
    }
  },

  getText : function()
  {
    try {
      if (this.kind == 'list') {
        var menu = this.input;
        return menu.options[menu.selectedIndex].text;
      }
      // non-list
      return this.input.value;
    }
    catch (err) {
      logError(err,'inplace.getText');
    }
  },

  getValue : function()
  {
    try {
        var menu = this.input;
        return menu.options[menu.selectedIndex].value;
    }
    catch (err) {
      logError(err,'inplace.getValue');
    }
  }
} // Inplace.prototype

Inplace.get = function(id)
{
  try {
    return Inplace.all[id];
  }
  catch (err) {
    logError(err,'inplace.get');
  }
}

Inplace.mouseOver = function(event)
{
  try {
    var element = eventSource(event,'inplace');
    var inplace = Inplace.all[element.inplace];
    if (inplace.kind == 'color') {
      element.style.fontWeight = 'bold';
    }
    else {
      element.style.backgroundColor = inplace.highlightColor;
    }
    element.style.cursor = 'pointer';
  }
  catch (err) {
    logError(err,'inplace.Inplace.mouseOver');
  }
}

Inplace.MouseOut = function(event)
{
  try {
    var element = eventSource(event,'inplace');
    var inplace = Inplace.all[element.inplace];
    if (inplace.kind == 'color') {
      element.style.fontWeight = 'normal';
    }
    else {
      element.style.backgroundColor = inplace.originalBackground;
    }
    element.style.cursor = inplace.originalCursor;
  }
  catch (err) {
    logError(err,'inplace.inplace.MouseOut');
  }
}

Inplace.click = function(event)
{
  try {
    Inplace.all[eventSource(event,'inplace').inplace].open();
  }
  catch (err) {
    logError(err,'inplace.inplaceClick');
  }
}

Inplace.defaultOk = function(event)
{
  try {
    cancelPropagation(event);
    var element = eventSource(event,'inplace');
    var editor = Inplace.all[element.inplace];
    if (editor.kind == 'date') {
      editor.picker.close();
    }
    else if (editor.kind == 'color') {
      editor.colorPicker.hidePicker();
    }
    editor.onOk(editor);
    return false;
  }
  catch (err) {
    logError(err,'inplace.inplaceDefaultOk');
  }
}

Inplace.defaultCancel = function(event)
{
  try {
    cancelPropagation(event);
    var element = eventSource(event,'inplace');
    var inplace = Inplace.all[element.inplace];
    if (inplace.kind == 'date') {
      inplace.picker.close();
    }
    else if (inplace.kind == 'color') {
      inplace.colorPicker.hidePicker();
    }
    inplace.onCancel();
    return false;
  }
  catch (err) {
    logError(err,'inplace.inplaceDefaultCancel');
  }
}

// functions for server-side inplace editor generators
Inplace.setHandler = function(serverScript,extras)
{
  Inplace.serverScript=serverScript;
  Inplace.extra = extras || {};
}

Inplace.standardRequest = function(inplace)
{
  try {
    var text = inplace.getText();
    if (inplace.oldText == text) {
      alert2('The value has not changed, nothing to do!');
      return;
    }
    if (inplace.confirm_after && !confirm(inplace.confirm_after)) {
      return;
    }
    var pars = {'inplace:id':inplace.id,'inplace:value':text};
    for (var key in Inplace.extra) {
      pars[key] = Inplace.extra[key];
    }
    if (inplace.kind == 'list') {
      pars['inplace:text'] = text;
      pars['inplace:value'] = inplace.getValue();
    }
    document.body.style.cursor = 'wait';
    loadObject(Inplace.serverScript,
               Inplace.standardReply,
               pars);
  }
  catch (err) {
    logError(err,'inplace.standardRequest');
  }
} // Inplace.standardRequest

Inplace.standardReply = function(response)
{
  try {
    document.body.style.cursor = 'default';
    if (response.report) {
      report(response.report);
      Inplace.get(response.id).showText(response.value,response.text);
    }
  }
  catch (err) {
    logError(err,'inplace.standardReply');
  }
} // Inplace.standardReply

Inplace.addImage = function(element)
{
  try {
    var editImage = $_('img',{src : '/images/inedit.png', className: 'editor' }, false,false);
    if (element.hasChildNodes()) {
      element.insertBefore(editImage,element.firstChild);
    }
    else {
      element.appendChild(editImage);
    }
  }
  catch (err) {
    logError(err,'inplace.addImage');
  }
} // Inplace.addImage
