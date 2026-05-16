package config

import (
	"bufio"
	"log"
	"os"
	"strings"
)

// LoadEnv loads environment variables from a .env file
// It does not override existing environment variables
func LoadEnv(filepath string) error {
	file, err := os.Open(filepath)
	if err != nil {
		// .env file is optional, so just log and continue
		if os.IsNotExist(err) {
			log.Printf("[Config] No .env file found at %s, using system environment variables", filepath)
			return nil
		}
		return err
	}
	defer file.Close()

	log.Printf("[Config] Loading environment variables from %s", filepath)

	scanner := bufio.NewScanner(file)
	lineNum := 0
	loadedCount := 0

	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Parse KEY=VALUE format
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			log.Printf("[Config] Warning: Invalid format at line %d: %s", lineNum, line)
			continue
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		// Remove quotes if present
		value = strings.Trim(value, `"'`)

		// Only set if not already in environment (system env takes precedence)
		if os.Getenv(key) == "" {
			os.Setenv(key, value)
			loadedCount++
		}
	}

	if err := scanner.Err(); err != nil {
		return err
	}

	log.Printf("[Config] Loaded %d environment variables from .env file", loadedCount)
	return nil
}

// Made with Bob
