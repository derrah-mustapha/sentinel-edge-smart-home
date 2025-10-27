# Dashboard Testing Guide

## Quick Start

### 1. Start the Application
```bash
cd /home/zakaria/Music/S2/projet/sentinel-edge-smart-home/dashboard/web
pip install -r requirements.txt  # If not already installed
python server.py
```

The app will be available at: **http://localhost:5000**

### 2. First-Time Login

**Option A: Using Default Admin**
- Username: `admin`
- Password: `password`

**Option B: Create New Account**
1. Click "Create one" on login page
2. Enter username (min 3 chars) and password (min 4 chars)
3. Confirm password
4. Click "Create Account"
5. You'll be automatically logged in

### 3. Dashboard Navigation

#### Header Bar
- **Logo:** Home button, system name
- **Connection Status:** Green dot = connected, Red = disconnected
- **User Info:** Shows current logged-in user
- **Logout:** Click to end session

#### Main Dashboard Sections

**System Status Card**
- MQTT broker connection status
- Last gesture input
- Last voice command
- Active topic count

**Quick Access Buttons**
- 🚨 Emergency: Activate emergency mode
- 🏠 Home Mode: Set home mode
- 🚗 Away Mode: Set away mode
- 😴 Sleep Mode: Set sleep mode

**Device States**
- Grid showing all connected device states
- Real-time updates as MQTT messages arrive
- Click the card to see more details

**Command Control**
- Organized by category (Door, Fan, Lights, Windows, Modes, Safety)
- One-click execution of predefined commands
- View command execution status

**Manual MQTT Publish**
- Advanced feature for testing
- Enter topic and payload
- Publish custom messages to broker

**Gesture Simulation**
- Simulate gesture detection
- Useful for testing gesture control flow
- Enter gesture token and click Simulate

**Voice Simulation**
- Simulate voice commands
- Test voice command processing
- Enter voice token and execute

**Topic Management**
- Subscribe to MQTT topics
- Enter pattern like `home/#`
- Unsubscribe when done
- View all active subscriptions below

**Message Log**
- Real-time MQTT message stream
- Color-coded: Time (green), Topic (blue), Payload (orange)
- Clear button to reset log
- Scrollable history

**Audit Log**
- Track all user actions
- Shows timestamp, user, and action
- Auto-updates with new actions

**Command History**
- Shows all executed commands
- Timestamp, user, command token, source, status
- Helps troubleshoot command issues

### 4. Testing Scenarios

#### Test User Registration
1. Logout (if logged in)
2. Go to `/register`
3. Create account with:
   - Username: `testuser`
   - Password: `testpass123`
4. Verify successful registration and auto-login

#### Test Dashboard Features
1. Ensure MQTT broker is running
2. Check device states update in real-time
3. Test command execution (watch audit log)
4. Simulate gestures and voices
5. Subscribe to topics and view updates
6. Publish custom messages

#### Test Responsiveness
1. **Desktop:** View full dashboard with all cards
2. **Tablet:** Switch to landscape (should be ~2 columns)
3. **Mobile:** Responsive single column layout
4. Resize browser window and verify layout adapts

#### Test Error Handling
1. Try registering with duplicate username → Should show error
2. Try logging in with wrong credentials → Should show error
3. Try password mismatch on register → Should show error
4. Enter missing required fields → Form validation prevents submit

### 5. Database

#### Database File Location
```
/home/zakaria/Music/S2/projet/sentinel-edge-smart-home/dashboard/web/dashboard_data.sqlite3
```

#### Tables Created
- `users` - User accounts with password hashes
- `mqtt_messages` - All MQTT messages received
- `state_latest` - Latest state for each topic
- `audit_events` - User action logs
- `command_events` - Command execution history

#### View Database Content (SQLite)
```bash
sqlite3 dashboard/web/dashboard_data.sqlite3
# List users:
SELECT username, created_ts FROM users;
# View audit log:
SELECT ts, user_name, action FROM audit_events ORDER BY ts DESC LIMIT 10;
```

### 6. Customization

#### Change Default Admin Credentials
```bash
export DASHBOARD_USER="myusername"
export DASHBOARD_PASS="mypassword"
python server.py
```

#### Change Flask Port
```python
# In server.py, change last line:
socketio.run(app, host='0.0.0.0', port=8000)
```

#### Add More Commands
Edit `COMMAND_CATALOG` in server.py:
```python
COMMAND_CATALOG = {
    'Lights': ['lights_on', 'lights_off', 'lights_dim'],
    'CustomGroup': ['custom_cmd1', 'custom_cmd2'],
}
```

### 7. Troubleshooting

**Problem: Login page appears but can't login**
- Check database file exists: `dashboard_data.sqlite3`
- Verify MQTT broker is running (optional)
- Check browser console for errors (F12)

**Problem: Real-time updates not showing**
- Confirm MQTT broker is accessible
- Check env vars: `MQTT_BROKER`, `MQTT_PORT`
- Subscribe to test topic and publish message

**Problem: Mobile layout looks broken**
- Clear browser cache (Ctrl+Shift+Delete)
- Ensure viewport meta tag is present in HTML
- Test in incognito/private mode

**Problem: Can't create new users**
- Check database permissions
- Verify username meets requirements (min 3 chars)
- Check password requirements (min 4 chars)
- Look for SQL errors in terminal

### 8. Performance Tips

- **Large MQTT volume:** Adjust MSG_LOG_MAX in server.py
- **Many users:** Consider using real auth (e.g., OAuth2)
- **Production:** Use reverse proxy (nginx) and HTTPS
- **Mobile:** Test with slow 3G throttling (Chrome DevTools)

### 9. Security Notes

⚠️ **For Production Use:**
1. Change default admin password
2. Use strong SECRET_KEY for Flask
3. Enable HTTPS/TLS for MQTT and web
4. Use proper CORS configuration
5. Implement rate limiting
6. Add proper user permissions/roles
7. Use environment variables for all secrets
8. Enable password reset functionality

### Hot Test Commands

```bash
# Check Flask is running
curl http://localhost:5000/login

# Check WebSocket connection
curl http://localhost:5000/

# Publish test message (if MQTT is running)
mosquitto_pub -t home/test -m "hello"

# Subscribe to all messages
mosquitto_sub -t home/#
```

## What Works ✓

- ✓ Beautiful responsive UI design
- ✓ User registration and authentication
- ✓ Real-time MQTT monitoring
- ✓ Command execution with audit logging
- ✓ Gesture and voice simulation
- ✓ Topic subscription management
- ✓ Message history logging
- ✓ Mobile-friendly layout
- ✓ Dark/light mode support
- ✓ WebSocket real-time updates
