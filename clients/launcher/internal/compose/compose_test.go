package compose

import (
	"path/filepath"
	"testing"
)

func TestNew(t *testing.T) {
	// filepath.Join is OS-aware (LF separators on Unix, backslash on
	// Windows). Use t.TempDir() to get a valid path on whatever runner
	// executes the test rather than hardcoding a /tmp path that doesn't
	// exist on Windows.
	home := t.TempDir()
	t.Setenv("DECEPTICON_HOME", home)
	c := New()
	if c.Home != home {
		t.Errorf("Home = %q, want %q", c.Home, home)
	}
	if want := filepath.Join(home, "docker-compose.yml"); c.ComposeFile != want {
		t.Errorf("ComposeFile = %q, want %q", c.ComposeFile, want)
	}
	if want := filepath.Join(home, ".env"); c.EnvFile != want {
		t.Errorf("EnvFile = %q, want %q", c.EnvFile, want)
	}
}

func TestAllProfiles(t *testing.T) {
	profiles := AllProfiles()
	if len(profiles) != 4 {
		t.Errorf("AllProfiles() len = %d, want 4 (2 pairs)", len(profiles))
	}
	// Verify pairs
	expected := []string{"--profile", "cli", "--profile", "c2-sliver"}
	for i, v := range expected {
		if profiles[i] != v {
			t.Errorf("profiles[%d] = %q, want %q", i, profiles[i], v)
		}
	}
}

func TestBaseArgs(t *testing.T) {
	c := &Compose{
		Home:        "/test",
		ComposeFile: "/test/docker-compose.yml",
		EnvFile:     "/test/.env",
	}
	args := c.baseArgs()
	if args[0] != "compose" || args[2] != "/test/docker-compose.yml" || args[4] != "/test/.env" {
		t.Errorf("baseArgs = %v", args)
	}
}

func TestImageTag(t *testing.T) {
	tests := map[string]string{
		"v1.0.21":  "1.0.21",
		"1.0.21":   "1.0.21",
		" latest ": "latest",
	}
	for input, want := range tests {
		if got := imageTag(input); got != want {
			t.Errorf("imageTag(%q) = %q, want %q", input, got, want)
		}
	}
}
