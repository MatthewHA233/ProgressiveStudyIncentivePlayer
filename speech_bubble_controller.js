/**
 * 33娘对话气泡控制脚本
 * 根据学习状态智能控制对话气泡的显示和内容
 */

// 配置项
const BUBBLE_CONFIG = {
  // 检查间隔（毫秒）
  CHECK_INTERVAL: 5000, // 5秒检查一次
  // 随机触发概率
  EFFICIENT_CHANCE: 0.05, // 高效状态下触发EFFICIENT台词的概率
  // 音频文件路径
  AUDIO_PATH: './audio33/',
  // CSV文件URL（相对或绝对路径）
  CSV_URL: './statistics/five_minute_logs/五分钟记录_' + getTodayDateString() + '.csv',
  // 备用CSV文件URL（如果当天文件不存在）
  FALLBACK_CSV_URL: './statistics/five_minute_logs/五分钟记录_2025-04-30.csv',
  // 悬浮按钮数据JSON路径
  BUTTON_DATA_PATH: './floating_button_data.json',
  // 学习状态存储键
  STORAGE_KEY: 'study_status_history',
  // 最大存储记录数
  MAX_HISTORY: 10,
  // 时间阈值（分钟）
  TIME_THRESHOLD: 7,
  // DEFAULT台词重复间隔（毫秒）
  DEFAULT_REPEAT_INTERVAL: 300000 // 5分钟
};

// 台词配置
const SPEECH_CONFIG = {
  // 表情吐槽台词
  EXPRESSIONS_COMMENTS: {
    DEFAULT: [
      { jp: "にゃん〜ご主人様、今日の計画表は食べられちゃったのかな？(°∀°)ﾉ", zh: "喵~主人今天的计划表被吃掉了嘛？(°∀°)ﾉ" },
      { jp: "びっくり！ご主人様はトマトタイマーを忘れましたにゃ！(ﾟДﾟ≡ﾟДﾟ)", zh: "惊诧！呆毛竖起来了！主人忘记开番茄钟啦！(ﾟДﾟ≡ﾟДﾟ)" }
    ],
    NORMAL: [
      { jp: "ふんふん〜ご主人様がサボってたらさんさんはわかるんだよ！(¬‿¬ )", zh: "哼哼~主人在摸鱼的话33会知道的哦！(¬‿¬ )" },
      { jp: "注意力の波動を検知〜落ち着きのない手を押さえてあげましょうか？(´• ω •`)", zh: "检测到注意力波动~要帮忙按住躁动的小手吗？(´• ω •`)" },
      { jp: "ご主人様の視線が本から逸れているのを検知！Σ(っ°Д°;)っ", zh: "检测到主人视线偏离书本！Σ(っ°Д°;)っ" },
      { jp: "小さな爪でタイマーを押さえられなくなっちゃう！(´；ω；`)", zh: "小爪子快要按不住计时器啦！(´；ω；`)" }
    ],
    EFFICIENT: [
      { jp: "すごい！ご主人様の集中力が輝いてるよ！✧*｡٩(ˊωˋ*)و✧*｡", zh: "好厉害！主人的专注力在发光耶！✧*｡٩(ˊωˋ*)و✧*｡" },
      { jp: "効率が限界突破！さんさんをハグで褒美してくれませんか？(⁄ ⁄•⁄ω⁄•⁄ ⁄)", zh: "效率突破天际！要奖励33一个抱抱吗？(⁄ ⁄•⁄ω⁄•⁄ ⁄)" }
    ]
  },
  // 学习过程吐槽
  LEARNING_COMMENTS: {
    START: [
      { jp: "ピンポーン！学習結界展開！( •̀ ω •́ )✧", zh: "叮~！学习结界展开！( •̀ ω •́ )✧" },
      { jp: "脳力全開モード起動！さんさんはご主人様のノートを取りますにゃ〜ฅ^•ω•^ฅ", zh: "脑力全开模式启动！33会帮主人记笔记的喵~ฅ^•ω•^ฅ" }
    ],
    LONG_SESSION: [
      { jp: "90分以上連続で勉強してますにゃ〜キャットニップエネルギー補給しますか？(=´ω｀=)", zh: "连续学习超过90分钟啦~要补充猫薄荷能量吗？(=´ω｀=)" },
      { jp: "ご主人様、ちょっと休憩しましょう〜さんさんのしっぽがしびれちゃいます〜(>_<)", zh: "主人休息一下嘛~33的尾巴要坐麻了啦~(>_<)" }
    ]
  },
  // 学习时长梯度
  STUDY_DURATION_LEVELS: [
    { range: [0, 1.5],   level: 'C',   theme: '理想、进取' },
    { range: [1.5, 3],   level: 'CC',  theme: '梦想、梦境' },
    { range: [3, 4.5],   level: 'CCC', theme: '感伤、坚毅' },
    { range: [4.5, 6],   level: 'B',   theme: '意志、我的回合' },
    { range: [6, 7.5],   level: 'BB',  theme: '长途跋涉、星辰' },
    { range: [7.5, 9],   level: 'BBB', theme: '悲壮、地狱' },
    { range: [9, 10.5],  level: 'A',   theme: '觉醒、贯行' },
    { range: [10.5, 12], level: 'AA',  theme: '英雄之旅、怒斥' },
    { range: [12, 13],   level: 'AAA', theme: '全力以赴、神迹' },
    { range: [13, 13.5], level: 'S',   theme: '宝可梦爆燃OP' },
    { range: [13.5, 14], level: 'SS',  theme: '友情、羁绊' },
    { range: [14, 14.5], level: 'SSS', theme: '目标是宝可梦大师' }
  ],
  // 时长吐槽台词
  DURATION_COMMENTS: {
    C:   [
      { jp: "33号エンジン起動！ご主人様、初心者村を突破しますよ〜(๑•̀ㅂ•́)و✧", zh: "33号引擎启动！主人要突破新手村啦~(๑•̀ㅂ•́)و✧" },
      { jp: "初期装備チェック完了！鉛筆が魔法の杖に変身！✧(≖ ◡ ≖✿)", zh: "初始装备检查完毕！铅笔变成法杖吧！✧(≖ ◡ ≖✿)" }
    ],
    CC:  [
      { jp: "夢境接続成功！ご主人様のノートが光ってます！(✧ω✧)", zh: "梦境连接成功！主人的笔记在发光耶！(✧ω✧)" },
      { jp: "脳波増幅を検知しました！さんさんが思考アクセラレーターになって加速しますよ！(ﾉ≧∀≦)ﾉ", zh: "检测到脑波增幅~让33来当思考加速器吧！(ﾉ≧∀≦)ﾉ" }
    ],
    CCC: [
      { jp: "ここまで頑張った自分はとてもカッコいい！頭撫で褒美はいかがですか？(´•ω•̥`)", zh: "坚持到现在的自己超帅气！要摸摸头奖励吗？(´•ω•̥`)" },
      { jp: "知識バリア突破IIIタイプ！さんさんの補給パックいつでも準備完了！( •̀∀•́ )✧", zh: "知识屏障突破III型！33的补给包随时待命！( •̀∀•́ )✧" }
    ],
    B:   [
      { jp: "私のターン！難問を全て経験値に変えちゃいましょう！d(>ω< )b", zh: "进入我的回合！让难题全部变成经验值吧！d(>ω< )b" },
      { jp: "意志力チャージ500%！さんさんの戦術ゴーグル起動中！( •̀ ω •́ )✧", zh: "意志力充能500%！33的战术目镜启动中！( •̀ ω •́ )✧" }
    ],
    BB:  [
      { jp: "星々ナビゲーションモードON！ご主人様は銀河系で一番輝く星ですよ〜☆~(◍´꒳`◍)", zh: "星辰导航模式ON！主人是银河系最亮那颗星~☆~(◍´꒳`◍)" },
      { jp: "長旅の必需品：コーヒーとさんさんの応援プレイリスト！ヽ(✿ﾟ▽ﾟ)ノ", zh: "长途旅行必备：咖啡和33的应援歌单！ヽ(✿ﾟ▽ﾟ)ノ" }
    ],
    BBB: [
      { jp: "地獄難易度だってなんのその！さんさんがご主人様と一緒にダンジョン攻略します！(╬ Ò ‸ Ó)", zh: "地狱难度又怎样！33会陪主人一起刷副本的！(╬ Ò ‸ Ó)" },
      { jp: "覚醒！絶望を力に変えろ！伝説の称号「不滅の勇者」獲得だぁっ！٩(๑`^´๑)۶", zh: "悲壮感转化成功！获得限定皮肤「不灭の勇者」！٩(๑`^´๑)۶" }
    ],
    A:   [
      { jp: "覚醒プロトコルロード完了！知識の嵐よ、もっと激しく襲来せよ！(ﾉﾟ▽ﾟ)ﾉ", zh: "觉醒协议加载完毕！让知识风暴来得更猛烈吧！(ﾉﾟ▽ﾟ)ﾉ" },
      { jp: "貫行モード：教科書で全ての難問を切り裂け！(╯‵□′)╯︵┻━┻", zh: "贯行模式：用教科书劈开所有难题！(╯‵□′)╯︵┻━┻" }
    ],
    AA:  [
      { jp: "英雄の旅のBGM発動！これはご主人様専用テーマソング〜♪(^∇^*)", zh: "英雄之旅的BGM响起！这是主人的专属主题曲~♪(^∇^*)" },
      { jp: "光子砲チャージ！知識の黄昏に吼えろ——光の消滅に抗え！(╬▼д▼)ﾉｼ", zh: "光子炮充能！向知识的黄昏怒吼吧——Rage ,rage against the dying of light！(╬▼д▼)" }
    ],
    AAA: [
      { jp: "奇跡が現れる！ご主人様の今日の努力値が天を突き破りました！(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", zh: "神迹即将显现！主人今天的努力值突破天际啦！(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧" },
      { jp: "全サーバーお知らせ：学習の神プレイヤーが歴史を作っています！Σ(っ°Д°;)っ", zh: "全服公告：学霸玩家正在创造历史！Σ(っ°Д°;)っ" }
    ],
    S:   [
      { jp: "ピカチュウの10万ボルト！ご主人様の学習力が進化します！(≧∇≦)ﾉ彡☆", zh: "皮卡丘十万伏特！主人的学习力要进化啦！(≧∇≦)ﾉ彡☆" },
      { jp: "ゲットだぜ！次のジムバッジは確定ですね！( •̀ ω •́ )✧", zh: "Get☆Daze！下一个道馆徽章入手预定！( •̀ ω •́ )✧" }
    ],
    SS:  [
      { jp: "絆進化！ご主人様とさんさんのコンビ技は無敵です！(๑•̀ㅂ•́)و✧", zh: "羁绊进化！主人和33的组合技是无敌的！(๑•̀ㅂ•́)و✧" },
      { jp: "友情守護結界展開！サボり妖怪入場禁止！(◣_◢)", zh: "友情守护结界展开！偷懒妖怪禁止入内！(◣_◢)" }
    ],
    SSS: [
      { jp: "最終ターン！全ての知識ポイントをゲットする時が来ました！(≧∇≦)/~┴┴", zh: "最终回合！收服所有知识点的时刻到啦！(≧∇≦)/~┴┴" },
      { jp: "ポケモンマスターへの道で、さんさんはいつでも最強のパートナーです！٩(๑>◡<๑)۶", zh: "成为宝可梦大师的路上，33永远是最强搭档！٩(๑>◡<๑)۶" }
    ]
  }
};

// 学习状态历史
let studyHistory = [];

// 音频播放状态
let audioPlaying = false;
let currentAudio = null;

// 上次检测到的学习时长
let lastStudyTime = null;
// 上次触发DEFAULT台词的时间
let lastDefaultSpeechTime = 0;
// 是否处于未学习状态
let isInDefaultState = false;

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
 * 初始化函数
 */
function initSpeechBubble() {
  console.log('初始化33娘对话气泡控制');
  
  // 从本地存储加载历史记录
  loadStudyHistory();
  
  // 设置定期检查
  setInterval(checkAndUpdateSpeech, BUBBLE_CONFIG.CHECK_INTERVAL);
  
  // 立即执行一次检查
  setTimeout(checkAndUpdateSpeech, 3000);
}

/**
 * 加载学习状态历史
 */
function loadStudyHistory() {
  const savedHistory = localStorage.getItem(BUBBLE_CONFIG.STORAGE_KEY);
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
 * 保存学习状态历史
 */
function saveStudyHistory() {
  // 限制历史记录数量
  if (studyHistory.length > BUBBLE_CONFIG.MAX_HISTORY) {
    studyHistory = studyHistory.slice(-BUBBLE_CONFIG.MAX_HISTORY);
  }
  localStorage.setItem(BUBBLE_CONFIG.STORAGE_KEY, JSON.stringify(studyHistory));
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
  for (const level of SPEECH_CONFIG.STUDY_DURATION_LEVELS) {
    if (hours >= level.range[0] && hours < level.range[1]) {
      return level.level;
    }
  }
  return 'C'; // 默认等级
}

/**
 * 随机选择一个台词
 * @param {Array} comments 台词数组
 * @returns {Object} 选中的台词对象
 */
function getRandomComment(comments) {
  const index = Math.floor(Math.random() * comments.length);
  return comments[index];
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
        currentAudio.onended = null; // 清除旧的回调
        currentAudio.onerror = null; // 清除旧的回调
        currentAudio = null;
      }
      audioPlaying = false;
    }
    
    const audio = new Audio(`${BUBBLE_CONFIG.AUDIO_PATH}${audioName}.wav`);
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
    const url = `${BUBBLE_CONFIG.CSV_URL}?t=${timestamp}`;
    
    let response = await fetch(url);
    
    // 如果当天的文件不存在，使用默认状态
    if (!response.ok) {
      console.log('当天CSV文件不存在，使用默认状态');
      return { isStudying: false, isLongSessionActive: false, level: 'C', totalStudyHours: 0, studyTimeString: "0时0分" };
    }
    
    const content = await response.text();
    const lines = content.trim().split('\n');
    
    if (lines.length <= 1) {
      console.log('CSV文件没有数据记录');
      return { isStudying: false, isLongSessionActive: false, level: 'C', totalStudyHours: 0, studyTimeString: "0时0分" };
    }
    
    // --- 新增：检测连续学习90分钟 (18条记录) ---
    let isLongSessionActive = false;
    const MIN_RECORDS_FOR_LONG_SESSION = 18;

    function timeToMinutes(timeStr) { // "HH:MM"
        if (!timeStr || !timeStr.includes(':')) return -1; // 基本的格式检查
        const parts = timeStr.split(':');
        if (parts.length !== 2) return -1;
        const hours = parseInt(parts[0], 10);
        const minutes = parseInt(parts[1], 10);
        if (isNaN(hours) || isNaN(minutes)) return -1;
        return hours * 60 + minutes;
    }

    if (lines.length > MIN_RECORDS_FOR_LONG_SESSION) { // 至少需要 1个头部 + 18个数据行
        const dataLines = lines.slice(1); // 跳过标题行
        if (dataLines.length >= MIN_RECORDS_FOR_LONG_SESSION) {
            const recent18Lines = dataLines.slice(-MIN_RECORDS_FOR_LONG_SESSION);
            let allConsecutiveAndFiveMinApart = true;
            for (let i = 0; i < recent18Lines.length; i++) {
                const currentLineParts = recent18Lines[i].split(',');
                if (currentLineParts.length < 1 || !currentLineParts[0]) { // 检查行和时间数据是否存在
                    allConsecutiveAndFiveMinApart = false;
                    break;
                }

                if (i > 0) {
                    const prevLineParts = recent18Lines[i-1].split(',');
                     if (prevLineParts.length < 1 || !prevLineParts[0]) {
                        allConsecutiveAndFiveMinApart = false;
                        break;
                    }
                    const prevTimeStr = prevLineParts[0];
                    const currentTimeStr = currentLineParts[0];

                    const prevMinutes = timeToMinutes(prevTimeStr);
                    const currentMinutes = timeToMinutes(currentTimeStr);

                    if (prevMinutes === -1 || currentMinutes === -1) { // 时间格式错误
                        allConsecutiveAndFiveMinApart = false;
                        break;
                    }

                    let diff = currentMinutes - prevMinutes;
                    // 处理午夜换日的情况 (例如从 23:55 到 00:00)
                    if (diff < 0 && Math.abs(diff) > (22 * 60)) { // 如果差异为负且绝对值很大，则假定为换日
                        diff += 24 * 60;
                    }

                    if (diff !== 5) {
                        allConsecutiveAndFiveMinApart = false;
                        break;
                    }
                }
            }
            if (allConsecutiveAndFiveMinApart) {
                isLongSessionActive = true;
                console.log("检测到连续学习90分钟！");
            }
        }
    }
    // --- 连续学习检测结束 ---

    const lastLine = lines[lines.length - 1];
    const [time, status] = lastLine.split(',');
    
    const now = new Date();
    const recordTimeParts = time ? time.split(':').map(Number) : [];
    const recordTime = new Date();
    if (recordTimeParts.length === 2 && !isNaN(recordTimeParts[0]) && !isNaN(recordTimeParts[1])) {
        recordTime.setHours(recordTimeParts[0], recordTimeParts[1], 0, 0);
    } else {
        // 如果时间格式不正确，则认为记录无效，可能不是在学习
        console.warn('CSV中最新记录的时间格式无效:', time);
        return { 
            isStudying: false, 
            isLongSessionActive: isLongSessionActive, // 即使最新记录无效，长时段检测可能仍然有效
            level: 'C', 
            totalStudyHours: 0, 
            studyTimeString: "0时0分" 
        };
    }
    
    const diffMs = now - recordTime;
    const timeDiff = Math.floor(diffMs / (1000 * 60));
    
    console.log(`最近记录时间: ${time}, 状态: ${status}, 时间差: ${timeDiff}分钟, 是否连续90分钟: ${isLongSessionActive}`);
    
    const buttonDataResponse = await fetch(`${BUBBLE_CONFIG.BUTTON_DATA_PATH}?t=${timestamp}`);
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
    if (timeDiff > BUBBLE_CONFIG.TIME_THRESHOLD) {
      return { 
        isStudying: false,
        level: level,
        totalStudyHours: totalStudyHours,
        studyTimeString: studyTimeString,
        isLongSessionActive: isLongSessionActive
      };
    }
    
    return {
      isStudying: true,
      isEfficient: status === '高效',
      level: level,
      totalStudyHours: totalStudyHours,
      studyTimeString: studyTimeString,
      isLongSessionActive: isLongSessionActive
    };
  } catch (error) {
    console.error('获取或处理CSV数据失败:', error);
    return { isStudying: false, isLongSessionActive: false, level: 'C', totalStudyHours: 0, studyTimeString: "0时0分" };
  }
}

/**
 * 根据条件选择并播放台词
 * @param {Object} currentStatus 当前学习状态
 * @param {Object} previousStatus 上一个学习状态
 * @param {boolean} studyTimeChanged 学习时长是否发生变化 (此参数在此函数内部不再严格依赖，因为调用处已处理)
 */
function selectAndPlaySpeech(currentStatus, previousStatus, studyTimeChanged) {
  if (audioPlaying) {
    console.log('已有音频正在播放，跳过本次台词选择');
    return;
  }
  
  console.log('选择台词 - 当前状态:', currentStatus, '上一状态:', previousStatus);

  // 优先处理 LONG_SESSION 状态
  // 当 isLongSessionActive 从 false 变为 true 时触发
  if (currentStatus.isLongSessionActive && (!previousStatus || !previousStatus.isLongSessionActive)) {
    const comments = SPEECH_CONFIG.LEARNING_COMMENTS.LONG_SESSION;
    const commentIndex = Math.floor(Math.random() * comments.length);
    const comment = comments[commentIndex];
    
    console.log("触发 LONG_SESSION 台词");
    playSpeechWithBubble(comment, 'LONG_SESSION', commentIndex); // 假设音频文件前缀为 LONG_SESSION
    return; // 最高优先级，播放后直接返回
  }
  
  // 1. 刚开始学习状态 (如果不是 LONG_SESSION)
  if (currentStatus.isStudying && (!previousStatus || !previousStatus.isStudying)) {
    const comments = SPEECH_CONFIG.LEARNING_COMMENTS.START;
    const commentIndex = Math.floor(Math.random() * comments.length);
    const comment = comments[commentIndex];
    
    console.log("触发 START 台词");
    playSpeechWithBubble(comment, 'START', commentIndex);
    return;
  }
  
  // 只有在学习状态下，并且不是刚开始学习或进入长时学习时，才判断以下内容
  if (currentStatus.isStudying) {
    // 2. 学习中但分心状态 (NORMAL)
    if (!currentStatus.isEfficient) {
      const comments = SPEECH_CONFIG.EXPRESSIONS_COMMENTS.NORMAL;
      const commentIndex = Math.floor(Math.random() * comments.length);
      const comment = comments[commentIndex];
      
      console.log("触发 NORMAL 台词");
      playSpeechWithBubble(comment, 'NORMAL', commentIndex);
      return;
    }
    
    // 3. 高效学习状态 (EFFICIENT 或 DURATION_COMMENTS)
    if (currentStatus.isEfficient) {
      // a. 5%概率触发EFFICIENT台词
      if (Math.random() < BUBBLE_CONFIG.EFFICIENT_CHANCE) {
        const comments = SPEECH_CONFIG.EXPRESSIONS_COMMENTS.EFFICIENT;
        const commentIndex = Math.floor(Math.random() * comments.length);
        const comment = comments[commentIndex];
        
        console.log("触发 EFFICIENT 台词 (随机)");
        playSpeechWithBubble(comment, 'EFFICIENT', commentIndex);
        return;
      }
      
      // b. 95%概率触发对应学习阶段的台词
      const level = currentStatus.level;
      if (SPEECH_CONFIG.DURATION_COMMENTS[level]) {
        const comments = SPEECH_CONFIG.DURATION_COMMENTS[level];
        const commentIndex = Math.floor(Math.random() * comments.length);
        const comment = comments[commentIndex];
        
        console.log(`触发 DURATION_COMMENTS (${level}) 台词`);
        playSpeechWithBubble(comment, level, commentIndex);
      } else {
        console.warn(`未找到等级 ${level} 的台词配置，使用C级台词`);
        const comments = SPEECH_CONFIG.DURATION_COMMENTS.C;
        const commentIndex = Math.floor(Math.random() * comments.length);
        const comment = comments[commentIndex];
        playSpeechWithBubble(comment, 'C', commentIndex);
      }
      return; // 确保在高效学习状态下有返回
    }
  }
  // console.log("没有合适的台词被触发");
}

/**
 * 检查学习状态并更新对话气泡
 */
async function checkAndUpdateSpeech() {
  try {
    const currentStatus = await fetchStudyStatus();
    const studyTimeChanged = lastStudyTime !== currentStatus.studyTimeString;

    if (studyTimeChanged) {
      console.log(`学习时长变化: ${lastStudyTime} -> ${currentStatus.studyTimeString}`);
      lastStudyTime = currentStatus.studyTimeString;
    }
    
    const previousStatus = getPreviousStudyStatus(); // 获取包含 isLongSessionActive 的上一个状态
    
    // 决定是否将当前状态添加到历史记录
    let significantChange = false;
    if (!previousStatus) {
        significantChange = true;
    } else {
        if (previousStatus.isStudying !== currentStatus.isStudying ||
            previousStatus.isEfficient !== currentStatus.isEfficient ||
            // 检查 isLongSessionActive 是否有意义地改变了
            (previousStatus.isLongSessionActive === undefined && currentStatus.isLongSessionActive === true) || 
            (previousStatus.isLongSessionActive !== undefined && previousStatus.isLongSessionActive !== currentStatus.isLongSessionActive)) {
            significantChange = true;
        }
    }

    if (significantChange || studyTimeChanged) { // 如果有显著状态变化或学习时间变化，则记录
        // （如果仅 studyTimeChanged 但核心状态未变，是否记录取决于需求，目前significantChange已包含核心状态）
        // 为了确保 previousStatus.isLongSessionActive 在下次迭代中可用，即使只有 studyTimeChanged 也可能需要记录
        // 但如果状态完全一样，只是时间戳更新，则不需要重复记录。
        // 当前 significantChange 的定义应该足够。
        if (significantChange) {
             addStudyStatus(currentStatus);
        }
    }
    
    const now = new Date().getTime();
    
    if (!currentStatus.isStudying) {
      isInDefaultState = true;
      if (studyTimeChanged || (now - lastDefaultSpeechTime > BUBBLE_CONFIG.DEFAULT_REPEAT_INTERVAL)) {
        lastDefaultSpeechTime = now;
        const comments = SPEECH_CONFIG.EXPRESSIONS_COMMENTS.DEFAULT;
        const commentIndex = Math.floor(Math.random() * comments.length);
        const comment = comments[commentIndex];
        
        console.log("触发 DEFAULT 台词");
        playSpeechWithBubble(comment, 'DEFAULT', commentIndex);
      }
    } else { // 正在学习
      if (isInDefaultState) {
        isInDefaultState = false;
        // 从非学习转为学习，这是一个重要的触发点，selectAndPlaySpeech会处理
      }
      
      // 学习状态下，当学习时长变化 或 isLongSessionActive状态变化时，尝试播放台词
      const longSessionStateJustChanged = previousStatus ? (previousStatus.isLongSessionActive !== currentStatus.isLongSessionActive && currentStatus.isLongSessionActive === true) : currentStatus.isLongSessionActive;

      if (studyTimeChanged || longSessionStateJustChanged) {
        selectAndPlaySpeech(currentStatus, previousStatus, studyTimeChanged);
      } else {
        // console.log("学习状态，但时长未变且长时段状态未变，不触发台词");
      }
    }
  } catch (error) {
    console.error('检查和更新对话气泡失败:', error);
  }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initSpeechBubble);

// 导出函数供外部调用
window.showSpeechBubble = showSpeechBubble;
window.hideSpeechBubble = hideSpeechBubble;
window.checkAndUpdateSpeech = checkAndUpdateSpeech; 