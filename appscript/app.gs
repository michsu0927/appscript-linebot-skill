const CHANNEL_ACCESS_TOKEN = 'your_channel_access_token'

/**
 * 將 LINE Webhook 接收到的原始 JSON 內容寫入 Google Sheet 的 'POSTLog' 工作表。
 * * @param {string} rawContent LINE Webhook 傳送的原始 JSON 字串。
 */
/**
 * 將內容寫入 Google Sheet 的指定工作表。
 * 如果提供了 customRowsToWrite 陣列，則寫入該陣列中的數據；
 * 否則，寫入預設的 Timestamp 和 rawContent。
 * * @param {string} rawContent LINE Webhook 傳送的原始 JSON 字串（當 customRowsToWrite 為空時使用）。
 * @param {string} sheetName 要寫入的工作表名稱。
 * @param {Array<Array<any>>} customRowsToWrite 包含多個自訂數據列的陣列。
 */
function writeLogToSheet(rawContent, sheetName = 'POSTLog', customRowsToWrite = []) {
 
  // 1. 檢查並取得工作表
  // ----------------------------------------------------
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  
  // 嘗試取得工作表
  let sheet_to_write = spreadsheet.getSheetByName(sheetName);

  // 如果工作表不存在，則建立它並設定標題列
  if (!sheet_to_write) {
    Logger.log('Worksheet "' + sheetName + '" not found. Creating it now...');
    
    // 建立新工作表
    sheet_to_write = spreadsheet.insertSheet(sheetName);
    
    // 預設標題列（如果使用 customRowsToWrite，標題可能需要手動處理或假定已存在）
    sheet_to_write.appendRow(['Timestamp', 'Full JSON Payload']);
    //Logger.log('Worksheet "' + sheetName + '" created with default headers.');
  }
  
  // 2. 決定寫入的數據
  // ----------------------------------------------------
  
  let dataToWrite;
  
  if (customRowsToWrite && customRowsToWrite.length > 0) {
    // 情況 A: 使用自訂數據 (通常 customRowsToWrite 應是一個包含多個列的陣列)
    dataToWrite = customRowsToWrite;
    //Logger.log(`Writing ${customRowsToWrite.length} custom rows to sheet: ${sheetName}`);
    
  } else {
    // 情況 B: 使用預設的 rawContent 數據
    const timestamp = new Date(); 
    const defaultRow = [
      timestamp,
      rawContent 
    ];
    dataToWrite = [defaultRow]; // 即使只有一列，也包裝成陣列，方便後續統一處理
    //Logger.log('Writing default raw content row to sheet: ' + sheetName);
  }

  // 3. 寫入資料
  // ----------------------------------------------------
  
  if (dataToWrite.length > 0) {
    // 使用 getRange 和 setValues 進行批次寫入，效率更高
    const lastRow = sheet_to_write.getLastRow();
    const startRow = lastRow + 1;
    const numRows = dataToWrite.length;
    const numCols = dataToWrite[0].length; // 假設所有行有相同的欄位數
    
    // 檢查工作表是否為全新，getLastRow() 可能返回 0
    if (sheet_to_write.getRange(startRow, 1).isBlank()) {
        sheet_to_write.getRange(startRow, 1, numRows, numCols).setValues(dataToWrite);
    } else {
        // 應使用 appendRow 或 getRange(startRow, ... ) 來避免覆蓋
        // 由於我們使用了 lastRow + 1，所以理論上是安全的。
        sheet_to_write.getRange(startRow, 1, numRows, numCols).setValues(dataToWrite);
    }
  }

  // Logger.log('Write operation completed for sheet: ' + sheetName);
}


/**
 * 【排程維護函式】
 * 刪除名為 'POSTLog' 的工作表，然後重新建立它並設定標題列。
 * 此函式適用於設定 Apps Script 的計時器觸發器 (Time-driven trigger)。
 */
function cleanLogSheetBySchedule() {
  const sheetName = 'POSTLog';
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  
  Logger.log(`Starting log sheet cleanup: ${sheetName}`);
  
  // 1. 嘗試取得並刪除工作表
  const sheetToDelete = spreadsheet.getSheetByName(sheetName);

  if (sheetToDelete) {
    // 檢查是否為最後一個工作表，Apps Script 不允許刪除最後一個工作表。
    if (spreadsheet.getSheets().length > 1) {
      spreadsheet.deleteSheet(sheetToDelete);
      Logger.log(`Successfully deleted existing sheet: ${sheetName}`);
    } else {
      // 如果它是唯一的工作表，則清空內容而不是刪除。
      sheetToDelete.clearContents();
      sheetToDelete.clearFormats();
      Logger.log(`Sheet ${sheetName} is the only sheet. Cleared contents instead of deleting.`);
    }
  } else {
    Logger.log(`Sheet ${sheetName} not found. No need to delete.`);
  }

  // 2. 重新建立工作表 (調用 writeLogToSheet 函式來完成這一步)
  // 傳入一個空字串，觸發 writeLogToSheet 檢查並建立工作表，但不寫入實際的 Webhook 資料。
  writeLogToSheet('');
  Logger.log(`Sheet ${sheetName} recreated and header row ensured.`);
}


// Line Webhook 入口
function doPost(e) {
  try {
    const json = JSON.parse(e.postData.contents);
    const events = json.events;
   
    const rawContent = e.postData.contents;
    
    //writeLogToSheet(rawContent);

    //Logger.log('Successfully appended data to sheet: ' + sheetName);
    //
    Logger.log('Received POST request event: ' + JSON.stringify(json));
    
    events.forEach(event => {
      if (event.type === 'message' && event.message.type === 'text') {
        let user_text = event.message.text;
        //check 
        //@mydevBot
        // 檢查訊息是否精確地以 "@早安~~~~" 開頭
        if (user_text.startsWith('@mydevBot')) {
            //@mydevBot 才 Log
            writeLogToSheet(rawContent);
            // 只有當 '@mydevBot' 是訊息的第一個部分時，才會執行此處的邏輯
            //Logger.log("觸發：早安推送服務（在訊息最前面）");
            // 執行早安推送函式...getPicAndVideoByDate

          // 只有當 '@mydevBot' 是訊息的第一個部分時，才會執行此處的邏輯
            let videoObj = null;
            const replyToken = event.replyToken;

             // 1. 提取指令後的內容並清理空格
            const commandPrefix = '@mydevBot';
            // 取得 "@mydevBot" 後的所有文字，並移除前後空格
            const dateArgument = user_text.substring(commandPrefix.length).trim();
          
            //handleTextMessage(event);
            
        } else {
            // 否則，無論訊息中是否包含這個詞，都會執行其他邏輯
            console.log("訊息不以 '@mydevBot' 開頭，忽略。");
        }
      }
    });
    
    return ContentService.createTextOutput(JSON.stringify({status: 'ok'}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    console.error('doPost Error:', error);
    return ContentService.createTextOutput(JSON.stringify({status: 'error', message: error.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet() {
  // 1. 建議指定工作表名稱 "POSTLog"，避免 getActiveSheet() 因選錯分頁而抓錯資料
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("POSTLog");
  
  // 如果找不到名為 "POSTLog" 的工作表，則退回預設的啟用工作表
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  }
  
  // 2. 取得有資料的最後一列
  var lastRow = sheet.getLastRow();
  
  // 如果完全沒有資料，直接回傳空陣列
  if (lastRow < 1) {
    return ContentService.createTextOutput(JSON.stringify([]))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  // 取得 A1 到 C 欄最後一列的所有資料
  var data = sheet.getRange(1, 1, lastRow, 3).getValues();
  
  var result = [];
  
  // 3. 直接在程式碼中定義固定的 Key 名稱（解決試算表第一列就是數據的問題）
  var headers = ["Timestamp", "Full JSON Payload", "Done"];
  
  // 4. 從第一列 (index 0) 開始迴圈處理每一筆資料，這樣才不會漏掉第一筆
  for (var i = 0; i < data.length; i++) {
    var row = data[i];
    Logger.log(row);
    var obj = {};
    
    // 寫入 Timestamp (A欄)
    obj[headers[0]] = row[0]; 
    
    // 寫入 Full JSON Payload (B欄)
    // 嘗試將字串解析為真實的 JSON 物件，避免變成帶有跳脫字元的字串
    try {
      obj[headers[1]] = JSON.parse(row[1]); 
    } catch (e) {
      // 如果該儲存格不是合法的 JSON 格式，則保留原始字串
      obj[headers[1]] = row[1];
    }
    
    // 寫入 Done (C欄)
    obj[headers[2]] = row[2]; 
    
    result.push(obj);
  }
  
  Logger.log(JSON.stringify(result));
  
  // 5. 轉換成 JSON 字串，並設定正確的 MimeType 回傳
  return ContentService.createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}