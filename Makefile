.PHONY: up clean fix build

up:
	@echo "🧩 Ortam temizliği ve servis başlatma başlıyor..."
	@bash ./fix_docker_ports.sh

clean:
	@bash ./fix_docker_ports.sh

fix:
	@bash ./fix_docker_ports.sh

build:
	@echo "⚙️  Docker imajı optimize edilerek oluşturuluyor..."
	@docker compose build --progress=plain --build-arg BUILDKIT_INLINE_CACHE=1

