/**
 * 33娘表情控制脚本
 * 根据最近的五分钟记录CSV文件来决定使用哪个33娘表情
 */

// 配置项
const CONFIG = {
  // CSV文件URL（相对或绝对路径）
  CSV_URL: './statistics/five_minute_logs/五分钟记录_' + getTodayDateString() + '.csv',
  // 备用CSV文件URL（如果当天文件不存在）
  FALLBACK_CSV_URL: './statistics/five_minute_logs/五分钟记录_2025-04-30.csv',
  // 表情映射
  EXPRESSIONS: {
    DEFAULT: '7', // 默认惊诧表情
    NORMAL: '1',  // 普通状态 - 生气表情
    EFFICIENT: '2' // 高效状态 - 开心表情
  },
  // 时间阈值（分钟）
  TIME_THRESHOLD: 7,
  // 更新频率（毫秒）
  UPDATE_INTERVAL: 5000 // 5秒
};

/**
 * 获取今天的日期字符串，格式为YYYY-MM-DD
 * @returns {string} 今天的日期字符串
 */
function getTodayDateString() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 从CSV文件名中提取日期
 * @param {string} fileName CSV文件名
 * @returns {string|null} 日期字符串，格式为YYYY-MM-DD
 */
function getDateFromFileName(fileName) {
  const match = fileName.match(/五分钟记录_(\d{4}-\d{2}-\d{2})\.csv/);
  return match ? match[1] : null;
}

/**
 * 获取CSV数据
 * @returns {Promise<Object>} 包含CSV数据和文件名的对象
 */
async function fetchCsvData() {
  try {
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    const url = `${CONFIG.CSV_URL}?t=${timestamp}`;
    
    let response = await fetch(url);
    
    // 如果当天的文件不存在，直接返回null，不尝试使用备用文件
    if (!response.ok) {
      console.log('当天CSV文件不存在，使用惊诧表情');
      return { content: null, fileName: null };
    }
    
    const content = await response.text();
    // 从URL中提取文件名
    const fileName = response.url.split('/').pop().split('?')[0];
    return { content, fileName };
  } catch (error) {
    console.error('获取CSV数据失败:', error);
    return { content: null, fileName: null };
  }
}

/**
 * 解析CSV内容并获取最近的记录
 * @param {string} content CSV内容
 * @returns {Object|null} 最近的记录对象，包含时间和状态
 */
function getLatestRecord(content) {
  if (!content) return null;
  
  try {
    const lines = content.trim().split('\n');
    
    // 跳过标题行
    if (lines.length <= 1) {
      return null;
    }
    
    // 获取最后一行数据
    const lastLine = lines[lines.length - 1];
    const [time, status] = lastLine.split(',');
    
    return { time, status };
  } catch (error) {
    console.error('解析CSV内容失败:', error);
    return null;
  }
}

/**
 * 计算最近记录时间与当前时间的差值（分钟）
 * @param {string} timeStr 时间字符串，格式为HH:MM
 * @returns {number} 时间差（分钟）
 */
function getTimeDifference(timeStr) {
  const now = new Date();
  const [hours, minutes] = timeStr.split(':').map(Number);
  
  const recordTime = new Date();
  recordTime.setHours(hours, minutes, 0, 0);
  
  // 计算时间差（毫秒）
  const diffMs = now - recordTime;
  
  // 转换为分钟
  return Math.floor(diffMs / (1000 * 60));
}

/**
 * 获取应该使用的33娘表情编号
 * @returns {Promise<string>} 表情编号
 */
async function get33Expression() {
  // 获取CSV数据
  const { content, fileName } = await fetchCsvData();
  
  if (!content || !fileName) {
    console.log('未找到CSV文件，使用默认表情');
    return CONFIG.EXPRESSIONS.DEFAULT;
  }
  
  // 检查文件日期是否为今天
  const fileDate = getDateFromFileName(fileName);
  const todayDate = getTodayDateString();
  
  if (fileDate !== todayDate) {
    console.log('CSV文件不是今天的记录，使用默认表情');
    return CONFIG.EXPRESSIONS.DEFAULT;
  }
  
  // 获取最近的记录
  const latestRecord = getLatestRecord(content);
  if (!latestRecord) {
    console.log('未找到有效记录，使用默认表情');
    return CONFIG.EXPRESSIONS.DEFAULT;
  }
  
  // 计算时间差
  const timeDiff = getTimeDifference(latestRecord.time);
  
  // 如果时间差超过阈值，使用默认表情
  if (timeDiff > CONFIG.TIME_THRESHOLD) {
    console.log(`最近记录时间超过${CONFIG.TIME_THRESHOLD}分钟，使用默认表情`);
    return CONFIG.EXPRESSIONS.DEFAULT;
  }
  
  // 根据状态选择表情
  if (latestRecord.status === '高效') {
    console.log('最近状态为高效，使用开心表情');
    return CONFIG.EXPRESSIONS.EFFICIENT;
  } else {
    console.log('最近状态为普通，使用生气表情');
    return CONFIG.EXPRESSIONS.NORMAL;
  }
}

/**
 * 将表情编号写入URL参数
 */
async function updateUrlParameter() {
  const expressionNumber = await get33Expression();
  
  // 获取当前URL
  let url = new URL(window.location.href);
  let params = new URLSearchParams(url.search);
  
  // 更新clock参数，但保留其他参数
  params.set('clock', expressionNumber);
  
  // 更新URL，不刷新页面
  window.history.replaceState({}, '', `${url.pathname}?${params.toString()}`);
  
  // 更新页面上的表情
  const clockElement = document.getElementById('clock');
  if (clockElement) {
    // 确保保留"clock"类
    clockElement.className = `clock c${expressionNumber}`;
    console.log(`已设置类名: ${clockElement.className}`);
  } else {
    console.error('找不到clock元素');
  }
  
  console.log(`已更新33娘表情为: ${expressionNumber}`);
}

// 直接设置33娘表情，不依赖CSV文件
function set33Expression(expressionNumber) {
  console.log(`设置33娘表情: ${expressionNumber}`);
  
  // 更新页面上的表情
  const clockElement = document.getElementById('clock');
  if (clockElement) {
    // 确保保留"clock"类
    clockElement.className = `clock c${expressionNumber}`;
    console.log(`已设置类名: ${clockElement.className}`);
  } else {
    console.error('找不到clock元素');
  }
}

// 初始化函数
function init33() {
  console.log('初始化33娘表情控制');
  
  // 默认先设置一个表情，确保33娘显示
  set33Expression('2');
  
  // 尝试从URL获取表情参数
  const urlParams = new URLSearchParams(window.location.search);
  const clockParam = urlParams.get('clock');
  if (clockParam) {
    set33Expression(clockParam);
  }
  
  // 尝试获取CSV数据并更新表情
  fetchAndUpdateExpression();
  
  // 每5秒更新一次表情
  setInterval(fetchAndUpdateExpression, CONFIG.UPDATE_INTERVAL);
}

// 获取CSV数据并更新表情
async function fetchAndUpdateExpression() {
  try {
    console.log('尝试获取CSV数据...');
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    const url = `${CONFIG.CSV_URL}?t=${timestamp}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      console.log('当天CSV文件不存在，使用惊诧表情');
      set33Expression(CONFIG.EXPRESSIONS.DEFAULT);
      return;
    }
    
    const content = await response.text();
    console.log('成功获取CSV数据');
    
    // 解析CSV内容
    const lines = content.trim().split('\n');
    if (lines.length <= 1) {
      console.log('CSV文件没有数据记录');
      set33Expression(CONFIG.EXPRESSIONS.DEFAULT);
      return;
    }
    
    // 获取最后一行数据
    const lastLine = lines[lines.length - 1];
    const [time, status] = lastLine.split(',');
    
    // 计算时间差
    const now = new Date();
    const [hours, minutes] = time.split(':').map(Number);
    const recordTime = new Date();
    recordTime.setHours(hours, minutes, 0, 0);
    const diffMs = now - recordTime;
    const timeDiff = Math.floor(diffMs / (1000 * 60));
    
    console.log(`最近记录时间: ${time}, 状态: ${status}, 时间差: ${timeDiff}分钟`);
    
    // 根据时间差和状态选择表情
    if (timeDiff > CONFIG.TIME_THRESHOLD) {
      console.log(`时间差超过${CONFIG.TIME_THRESHOLD}分钟，使用默认表情`);
      set33Expression(CONFIG.EXPRESSIONS.DEFAULT);
    } else if (status === '高效') {
      console.log('最近状态为高效，使用开心表情');
      set33Expression(CONFIG.EXPRESSIONS.EFFICIENT);
    } else {
      console.log('状态为普通，使用生气表情');
      set33Expression(CONFIG.EXPRESSIONS.NORMAL);
    }
  } catch (error) {
    console.error('获取或处理CSV数据失败:', error);
    // 出错时使用默认表情
    set33Expression(CONFIG.EXPRESSIONS.DEFAULT);
  }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', init33);

// 导出函数供外部调用
window.set33Expression = set33Expression;
window.fetchAndUpdateExpression = fetchAndUpdateExpression; 