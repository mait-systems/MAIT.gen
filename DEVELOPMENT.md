# Development Workflow

## For Developer (Yarik)

### Working Across Multiple Machines

1. **Pull Latest Code**:
   ```bash
   git pull origin main
   ```

2. **Your Private Development Files** (not in git):
   - `CLAUDE.md` - Claude development notes and instructions
   - `PROJECT_MEMORY.md` - Session memory and technical notes  
   - `.claude/` - Claude settings and configuration
   - `generator_config.yaml` - Your real credentials (template is in git)

3. **Key Commands**:
   ```bash
   # Quick deployment test
   docker compose up --build -d
   
   # Check logs
   docker compose logs -f
   
   # Stop services  
   docker compose down
   ```

### Development Setup on New Machine

1. Clone repository:
   ```bash
   git clone https://github.com/mait-systems/MAIT.gen.git
   cd MAIT.gen
   ```

2. Copy your private development files from secure backup:
   - `CLAUDE.md`
   - `PROJECT_MEMORY.md` 
   - `.claude/settings.local.json`
   - `generator_config.yaml` (with real credentials)

3. Test deployment:
   ```bash
   docker compose up --build -d
   ```

## For End Users

Users get a clean repository without development files:

```bash
git clone https://github.com/mait-systems/MAIT.gen.git
cd MAIT.gen
cp generator_config.yaml.example generator_config.yaml
# Edit generator_config.yaml with their settings
docker compose up --build -d
```

## Files Excluded from Git

- Development files: `CLAUDE.md`, `PROJECT_MEMORY.md`, `.claude/`
- Credentials: `generator_config.yaml`, `.env` files
- Logs: `*.log` files
- Build artifacts: `node_modules/`, `__pycache__/`, etc.