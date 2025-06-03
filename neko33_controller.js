/**
 * 33娘统一控制器 - 整合表情和对话气泡功能
 * 同时控制33娘的表情动画和对话气泡显示
 */

// 主要配置项
const NEKO33_CONFIG = {
  // CSV文件URL（相对或绝对路径）
  CSV_URL: './statistics/five_minute_logs/五分钟记录_' + getTodayDateString() + '.csv',
  // 备用CSV文件URL（如果当天文件不存在）
  FALLBACK_CSV_URL: './statistics/five_minute_logs/五分钟记录_2025-04-30.csv',
  // 台词数据文件路径
  SPEECH_DATA_PATH: './speech_data.json',
  // 悬浮按钮数据JSON路径
  BUTTON_DATA_PATH: './floating_button_data.json',
  // 表情映射
  EXPRESSIONS: {
    DEFAULT: '7', // 默认惊诧表情
    NORMAL: '1',  // 普通状态 - 生气表情
    EFFICIENT: '2' // 高效状态 - 开心表情
  },
  // 时间阈值（分钟）
  TIME_THRESHOLD: 7,
  // 检查间隔（毫秒）
  CHECK_INTERVAL: 5000, // 5秒检查一次
  // 学习状态存储键
  STORAGE_KEY: 'study_status_history',
  // 最大存储记录数
  MAX_HISTORY: 10
};

// 全局变量
let speechData = null; // 台词数据
let studyHistory = []; // 学习状态历史
let audioPlaying = false; // 音频播放状态
let currentAudio = null; // 当前播放的音频
let lastStudyTime = null; // 上次检测到的学习时长
let lastDefaultSpeechTime = 0; // 上次触发DEFAULT台词的时间
let isInDefaultState = false; // 是否处于未学习状态

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
 * 加载台词数据
 * @returns {Promise<boolean>} 是否加载成功
 */
async function loadSpeechData() {
  try {
    const timestamp = new Date().getTime();
    const response = await fetch(`${NEKO33_CONFIG.SPEECH_DATA_PATH}?t=${timestamp}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    speechData = await response.json();
    console.log('台词数据加载成功');
    return true;
  } catch (error) {
    console.error('加载台词数据失败:', error);
    return false;
  }
}

/**
 * 从本地存储加载学习状态历史
 */
function loadStudyHistory() {
  const savedHistory = localStorage.getItem(NEKO33_CONFIG.STORAGE_KEY);
  if (savedHistory) {
    try {
      studyHistory = JSON.parse(savedHistory);
      console.log('已加载学习状态历史:', studyHistory);
    } catch (e) {
      console.error('解析学习状态历史失败:', e);
      studyHistory = [];
    }
  }
}

/**
 * 保存学习状态历史到本地存储
 */
function saveStudyHistory() {
  // 限制历史记录数量
  if (studyHistory.length > NEKO33_CONFIG.MAX_HISTORY) {
    studyHistory = studyHistory.slice(-NEKO33_CONFIG.MAX_HISTORY);
  }
  localStorage.setItem(NEKO33_CONFIG.STORAGE_KEY, JSON.stringify(studyHistory));
}

/**
 * 添加学习状态记录
 * @param {Object} status 学习状态对象
 */
function addStudyStatus(status) {
  studyHistory.push({
    timestamp: new Date().getTime(),
    ...status
  });
  saveStudyHistory();
}

/**
 * 获取最新的学习状态
 * @returns {Object|null} 最新的学习状态
 */
function getLatestStudyStatus() {
  if (studyHistory.length === 0) {
    return null;
  }
  return studyHistory[studyHistory.length - 1];
}

/**
 * 获取上一个学习状态
 * @returns {Object|null} 上一个学习状态
 */
function getPreviousStudyStatus() {
  if (studyHistory.length < 2) {
    return null;
  }
  return studyHistory[studyHistory.length - 2];
}

/**
 * 根据学习时长获取对应的等级
 * @param {number} hours 学习时长（小时）
 * @returns {string} 等级代码
 */
function getLevelByHours(hours) {
  if (!speechData || !speechData.study_duration_levels) {
    return 'C'; // 默认等级
  }
  
  for (const level of speechData.study_duration_levels) {
    if (hours >= level.range[0] && hours < level.range[1]) {
      return level.level;
    }
  }
  return 'C'; // 默认等级
}

/**
 * 设置33娘表情（不依赖CSV文件）
 * @param {string} expressionNumber 表情编号
 */
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

/**
 * 播放音频
 * @param {string} audioName 音频文件名（不含扩展名）
 * @returns {Promise} 音频播放完成后的Promise
 */
function playAudio(audioName) {
  return new Promise((resolve, reject) => {
    if (audioPlaying) {
      // 如果有音频正在播放，停止它
      if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
      }
      audioPlaying = false;
    }
    
    const audioPath = speechData?.config?.audio_path || './audio33/';
    const audio = new Audio(`${audioPath}${audioName}.wav`);
    currentAudio = audio;
    
    audio.onended = function() {
      audioPlaying = false;
      currentAudio = null;
      resolve();
    };
    
    audio.onerror = function(e) {
      console.error(`播放音频失败: ${audioName}.wav`, e);
      audioPlaying = false;
      currentAudio = null;
      reject(e);
    };
    
    audioPlaying = true;
    audio.play().catch(e => {
      console.error(`开始播放音频失败: ${audioName}.wav`, e);
      audioPlaying = false;
      currentAudio = null;
      reject(e);
    });
  });
}

/**
 * 显示对话气泡
 * @param {string} text 显示的文本
 * @param {number} duration 显示时长（毫秒），如果为null则不自动隐藏
 */
function showSpeechBubble(text, duration = null) {
  const bubble = document.getElementById('speech_bubble');
  if (!bubble) {
    console.error('找不到speech_bubble元素');
    return;
  }
  
  bubble.innerHTML = text;
  bubble.style.display = 'block';
  
  if (duration) {
    setTimeout(() => {
      bubble.style.display = 'none';
    }, duration);
  }
}

/**
 * 隐藏对话气泡
 */
function hideSpeechBubble() {
  const bubble = document.getElementById('speech_bubble');
  if (bubble) {
    bubble.style.display = 'none';
  }
}

/**
 * 播放台词并显示气泡
 * @param {Object} comment 台词对象，包含jp和zh属性
 * @param {string} audioPrefix 音频文件前缀
 * @param {number} index 台词索引
 */
async function playSpeechWithBubble(comment, audioPrefix, index) {
  if (audioPlaying) {
    console.log('已有音频正在播放，跳过本次播放');
    return;
  }
  
  try {
    // 显示日文台词并播放日文音频
    showSpeechBubble(comment.jp);
    await playAudio(`${audioPrefix}${index + 1}`);
    
    // 等待1秒后显示中文台词并播放中文音频
    setTimeout(async () => {
      showSpeechBubble(comment.zh);
      
      try {
        await playAudio(`${audioPrefix}${index + 1}中`);
        // 音频播放完成后隐藏气泡
        hideSpeechBubble();
      } catch (e) {
        console.error('播放中文音频失败', e);
        // 出错时也要隐藏气泡
        setTimeout(hideSpeechBubble, 2000);
      }
    }, 1000);
  } catch (e) {
    console.error('播放日文音频失败', e);
    // 出错时也要隐藏气泡
    setTimeout(hideSpeechBubble, 2000);
  }
}

/**
 * 从CSV文件获取学习状态
 * @returns {Promise<Object>} 学习状态对象
 */
async function fetchStudyStatus() {
  try {
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    const url = `${NEKO33_CONFIG.CSV_URL}?t=${timestamp}`;
    
    let response = await fetch(url);
    
    // 如果当天的文件不存在，使用默认状态
    if (!response.ok) {
      console.log('当天CSV文件不存在，使用默认状态');
      return { isStudying: false };
    }
    
    const content = await response.text();
    
    // 解析CSV内容
    const lines = content.trim().split('\n');
    
    // 跳过标题行
    if (lines.length <= 1) {
      console.log('CSV文件没有数据记录');
      return { isStudying: false };
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
    
    // 从floating_button_data.json获取学习时长信息
    const buttonDataResponse = await fetch(`${NEKO33_CONFIG.BUTTON_DATA_PATH}?t=${timestamp}`);
    let totalStudyHours = 0;
    let studyTimeString = "0时0分";
    
    if (buttonDataResponse.ok) {
      const buttonData = await buttonDataResponse.json();
      
      // 解析学习时长
      studyTimeString = buttonData.study_time;
      const studyTimeMatch = studyTimeString.match(/(\d+)时(\d+)分/);
      const studyHours = studyTimeMatch ? parseInt(studyTimeMatch[1]) : 0;
      const studyMinutes = studyTimeMatch ? parseInt(studyTimeMatch[2]) : 0;
      totalStudyHours = studyHours + (studyMinutes / 60);
    }
    
    // 根据学习时长确定等级
    const level = getLevelByHours(totalStudyHours);
    
    // 如果时间差超过7分钟，认为不在学习
    if (timeDiff > NEKO33_CONFIG.TIME_THRESHOLD) {
      return { 
        isStudying: false,
        level: level,
        totalStudyHours: totalStudyHours,
        studyTimeString: studyTimeString
      };
    }
    
    return {
      isStudying: true,
      isEfficient: status === '高效',
      level: level,
      totalStudyHours: totalStudyHours,
      studyTimeString: studyTimeString
    };
  } catch (error) {
    console.error('获取或处理CSV数据失败:', error);
    return { isStudying: false };
  }
}

/**
 * 根据条件选择并播放台词
 * @param {Object} currentStatus 当前学习状态
 * @param {Object} previousStatus 上一个学习状态
 * @param {boolean} studyTimeChanged 学习时长是否发生变化
 */
function selectAndPlaySpeech(currentStatus, previousStatus, studyTimeChanged) {
  // 如果台词数据未加载或有音频正在播放，不执行新的播放
  if (!speechData || audioPlaying) {
    console.log('台词数据未加载或已有音频正在播放，跳过本次检查');
    return;
  }
  
  console.log('当前状态:', currentStatus, '上一状态:', previousStatus, '时长变化:', studyTimeChanged);
  
  // 如果学习时长没有变化，不触发台词
  if (!studyTimeChanged && lastStudyTime !== null) {
    console.log('学习时长未变化，不触发台词');
    return;
  }
  
  // 1. 刚开始学习状态
  if (currentStatus.isStudying && (!previousStatus || !previousStatus.isStudying)) {
    const comments = speechData.learning_comments?.START || [];
    if (comments.length > 0) {
      const commentIndex = Math.floor(Math.random() * comments.length);
      const comment = comments[commentIndex];
      playSpeechWithBubble(comment, 'START', commentIndex);
    }
    return;
  }
  
  // 2. 学习中但分心状态
  if (currentStatus.isStudying && !currentStatus.isEfficient) {
    const comments = speechData.expressions_comments?.NORMAL || [];
    if (comments.length > 0) {
      const commentIndex = Math.floor(Math.random() * comments.length);
      const comment = comments[commentIndex];
      playSpeechWithBubble(comment, 'NORMAL', commentIndex);
    }
    return;
  }
  
  // 3. 高效学习状态
  if (currentStatus.isStudying && currentStatus.isEfficient) {
    const efficientChance = speechData.config?.efficient_chance || 0.05;
    
    // a. 5%概率触发EFFICIENT台词
    if (Math.random() < efficientChance) {
      const comments = speechData.expressions_comments?.EFFICIENT || [];
      if (comments.length > 0) {
        const commentIndex = Math.floor(Math.random() * comments.length);
        const comment = comments[commentIndex];
        playSpeechWithBubble(comment, 'EFFICIENT', commentIndex);
      }
      return;
    }
    
    // b. 95%概率触发对应学习阶段的台词
    const level = currentStatus.level;
    
    if (speechData.duration_comments && speechData.duration_comments[level]) {
      const comments = speechData.duration_comments[level];
      const commentIndex = Math.floor(Math.random() * comments.length);
      const comment = comments[commentIndex];
      
      playSpeechWithBubble(comment, level, commentIndex);
    } else {
      console.warn(`未找到等级 ${level} 的台词配置`);
      // 默认使用C级台词
      const comments = speechData.duration_comments?.C || [];
      if (comments.length > 0) {
        const commentIndex = Math.floor(Math.random() * comments.length);
        const comment = comments[commentIndex];
        playSpeechWithBubble(comment, 'C', commentIndex);
      }
    }
  }
}

/**
 * 检查学习状态并更新33娘的表情和对话气泡
 */
async function checkAndUpdate33() {
  try {
    // 获取当前学习状态
    const currentStatus = await fetchStudyStatus();
    
    // 检查学习时长是否发生变化
    const studyTimeChanged = lastStudyTime !== currentStatus.studyTimeString;
    
    // 更新上次检测到的学习时长
    if (studyTimeChanged) {
      console.log(`学习时长变化: ${lastStudyTime} -> ${currentStatus.studyTimeString}`);
      lastStudyTime = currentStatus.studyTimeString;
    }
    
    // 获取上一个学习状态
    const previousStatus = getPreviousStudyStatus();
    
    // 如果当前状态与上一个状态不同，则添加到历史记录
    if (!previousStatus || 
        previousStatus.isStudying !== currentStatus.isStudying || 
        previousStatus.isEfficient !== currentStatus.isEfficient) {
      addStudyStatus(currentStatus);
    }
    
    const now = new Date().getTime();
    const defaultRepeatInterval = speechData?.config?.default_repeat_interval || 300000;
    
    // 根据学习状态设置表情
    if (!currentStatus.isStudying) {
      // 未学习状态 - 设置默认表情
      set33Expression(NEKO33_CONFIG.EXPRESSIONS.DEFAULT);
      isInDefaultState = true;
      
      // 如果学习时长变化或者距离上次DEFAULT台词已经过了5分钟
      if (studyTimeChanged || (now - lastDefaultSpeechTime > defaultRepeatInterval)) {
        lastDefaultSpeechTime = now;
        const comments = speechData?.expressions_comments?.DEFAULT || [];
        if (comments.length > 0) {
          const commentIndex = Math.floor(Math.random() * comments.length);
          const comment = comments[commentIndex];
          playSpeechWithBubble(comment, 'DEFAULT', commentIndex);
        }
      }
    } 
    // 学习状态
    else {
      // 如果从未学习状态转为学习状态，重置标志
      if (isInDefaultState) {
        isInDefaultState = false;
      }
      
      // 根据效率设置表情
      if (currentStatus.isEfficient) {
        set33Expression(NEKO33_CONFIG.EXPRESSIONS.EFFICIENT);
      } else {
        set33Expression(NEKO33_CONFIG.EXPRESSIONS.NORMAL);
      }
      
      // 学习状态下，只有在学习时长变化时才触发台词
      if (studyTimeChanged) {
        selectAndPlaySpeech(currentStatus, previousStatus, studyTimeChanged);
      }
    }
  } catch (error) {
    console.error('检查和更新33娘状态失败:', error);
    // 出错时使用默认表情
    set33Expression(NEKO33_CONFIG.EXPRESSIONS.DEFAULT);
  }
}

/**
 * 初始化33娘控制器
 */
async function initNeko33Controller() {
  console.log('初始化33娘统一控制器');
  
  // 加载台词数据
  const speechLoaded = await loadSpeechData();
  if (!speechLoaded) {
    console.error('台词数据加载失败，将使用基础功能');
  }
  
  // 从本地存储加载历史记录
  loadStudyHistory();
  
  // 默认先设置一个表情，确保33娘显示
  set33Expression(NEKO33_CONFIG.EXPRESSIONS.EFFICIENT);
  
  // 尝试从URL获取表情参数
  const urlParams = new URLSearchParams(window.location.search);
  const clockParam = urlParams.get('clock');
  if (clockParam) {
    set33Expression(clockParam);
  }
  
  // 执行第一次检查
  setTimeout(checkAndUpdate33, 3000);
  
  // 设置定期检查
  setInterval(checkAndUpdate33, NEKO33_CONFIG.CHECK_INTERVAL);
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initNeko33Controller);

// 导出函数供外部调用
window.set33Expression = set33Expression;
window.showSpeechBubble = showSpeechBubble;
window.hideSpeechBubble = hideSpeechBubble;
window.checkAndUpdate33 = checkAndUpdate33; 