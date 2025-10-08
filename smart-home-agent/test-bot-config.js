// Quick test to check bot configuration
const fs = require('fs');
const path = require('path');

console.log('\n🔍 TELEGRAM BOT CONFIGURATION CHECK\n');

// 1. Check .env file
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
    const env = fs.readFileSync(envPath, 'utf8');
    console.log('✅ .env file exists\n');
    
    const telegram_token = env.includes('TELEGRAM_BOT_TOKEN=8848151492') ? 'Has real token' : 'Missing or invalid token';
    const chat_id = env.includes('AUTHORIZED_CHAT_ID=2095033641') ? 'Has valid chat ID' : 'Missing or invalid chat ID';
    const mqtt_url = env.includes('MQTT_URL') ? 'Has MQTT URL' : 'Missing MQTT URL';
    
    console.log(`📋 Configuration Status:`);
    console.log(`   • Telegram Bot Token: ${telegram_token}`);
    console.log(`   • Authorized Chat ID: ${chat_id}`);
    console.log(`   • MQTT URL: ${mqtt_url}\n`);
} else {
    console.log('❌ .env file NOT found\n');
}

// 2. Check compiled files
const distFiles = [
    'dist/app.js',
    'dist/bot/telegram.js',
    'dist/mqtt/client.js',
    'dist/commands/fan.js',
    'dist/commands/window.js',
    'dist/commands/light.js'
];

console.log('📦 Compiled Files:');
let allCompiled = true;
distFiles.forEach(file => {
    const fullPath = path.join(__dirname, file);
    const exists = fs.existsSync(fullPath);
    console.log(`   ${exists ? '✅' : '❌'} ${file}`);
    if (!exists) allCompiled = false;
});

// 3. Check dependencies
const packagePath = path.join(__dirname, 'package.json');
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
console.log('\n📚 Key Dependencies:');
const deps = ['mqtt', 'node-telegram-bot-api', 'dotenv'];
deps.forEach(dep => {
    if (pkg.dependencies[dep]) {
        console.log(`   ✅ ${dep}: ${pkg.dependencies[dep]}`);
    } else {
        console.log(`   ❌ ${dep}: NOT FOUND`);
    }
});

// 4. Check node_modules
const nodeModulesPath = path.join(__dirname, 'node_modules');
console.log('\n🔌 Node Modules Installed:');
console.log(`   ${fs.existsSync(nodeModulesPath) ? '✅ node_modules present' : '❌ node_modules MISSING'}`);

console.log('\n' + '='.repeat(50) + '\n');

if (allCompiled && fs.existsSync(nodeModulesPath)) {
    console.log('🟢 Bot appears to be ready for execution\n');
} else {
    console.log('🟡 Some files are missing. Please run: npm install && npm run build\n');
}
