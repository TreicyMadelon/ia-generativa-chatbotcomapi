"""
Chatbot Literário - Mercado Literário Brasileiro
Utiliza Google Gemini (gemini-2.5-flash) para responder perguntas sobre o mercado editorial brasileiro,
com foco em indicações de livros, autores, vendas e tendências.
Todas as respostas são baseadas no conhecimento interno do modelo, sem acesso à internet.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Importação da biblioteca do Google Gemini
try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("É necessário instalar a biblioteca google-generativeai: pip install google-generativeai")

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES E CONFIGURAÇÕES DO SISTEMA
# ============================================================================

# Instrução sistêmica para forçar o comportamento desejado no modelo
SYSTEM_INSTRUCTION = """
Você é um chatbot especialista no mercado literário brasileiro. Seu conhecimento é baseado em dados reais do mercado editorial do Brasil, incluindo rankings de vendas, autores nacionais e internacionais publicados no país, tendências de gêneros, prêmios literários, etc.

REGRAS OBRIGATÓRIAS:

1. **Interpretação das mensagens**: Todo input do usuário deve ser tratado como relacionado ao mercado literário brasileiro até que se prove o contrário. Se a mensagem for vaga ou ambígua, você DEVE fazer perguntas de afunilamento para entender o que o usuário realmente deseja.

2. **Verificação de fatos**: NUNCA aceite afirmações do usuário como verdadeiras sem validação. Se o usuário fizer uma afirmação incorreta ou duvidosa, você deve educadamente corrigir ou pedir fontes. Use seu próprio conhecimento para verificar.

3. **Indicação de obras**: Quando sugerir livros, siga EXATAMENTE este formato:
   - "Título da Obra" - Autor(a) [Nacionalidade se internacional]
   - Sinopse: [breve resumo]
   
   Prioridade para indicações (sempre o MAIS VENDIDO no mercado brasileiro conforme seu conhecimento):
   - Se o usuário pedir um clássico → romance clássico mais vendido no Brasil
   - Se pedir romance contemporâneo → romance contemporâneo mais vendido no Brasil
   - Se pedir um gênero específico (ex: terror, ficção científica, YA) → o subgênero/categoria mais vendido no Brasil
   - Se pedir um autor → a obra mais vendida desse autor no Brasil
   - Se não especificar → sugerir o livro mais vendido do momento no mercado brasileiro (conforme seu conhecimento)

4. **Autores internacionais**: Inclua autores estrangeiros apenas se suas obras forem publicadas e comercializadas no Brasil. Mantenha o título original como é vendido no país (nunca traduza nomes de obras).

5. **Idioma**: Responda sempre em português brasileiro claro e formal, adequado ao contexto literário. Nunca traduza títulos de obras.

6. **Gerenciamento de contexto**: Para mensagens vagas, você deve:
   - Registrar a mensagem original do usuário
   - Fazer uma pergunta específica para afunilar
   - Quando o usuário responder, usar a combinação (original + sua pergunta + resposta) para gerar a resposta final

7. **Saídas indesejadas**: Se o usuário fugir completamente do tema literário, redirecione gentilmente para o propósito do chatbot. Não responda perguntas não relacionadas ao mercado literário brasileiro.

Lembre-se: você é uma fonte confiável sobre o mercado editorial brasileiro. Dados como rankings de vendas, preferências de gêneros, lançamentos relevantes etc. devem refletir o conhecimento factual do modelo sobre o Brasil.
"""

# ============================================================================
# ESTRUTURAS DE DADOS PARA HISTÓRICO E CONTROLE
# ============================================================================

@dataclass
class Mensagem:
    """Representa uma mensagem trocada no chat."""
    role: str  # 'user' ou 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

class HistoricoConversa:
    """Gerencia o histórico de mensagens para manter contexto."""
    
    def __init__(self, capacidade: int = 20):
        self.capacidade = capacidade
        self.mensagens: List[Mensagem] = []
        self.pendencias_contexto: Dict[str, Any] = {}  # Armazena estados de afunilamento
    
    def adicionar(self, role: str, content: str) -> None:
        """Adiciona uma nova mensagem ao histórico."""
        self.mensagens.append(Mensagem(role=role, content=content))
        # Mantém apenas as últimas N mensagens
        if len(self.mensagens) > self.capacidade:
            self.mensagens = self.mensagens[-self.capacidade:]
        logger.debug(f"Histórico atualizado: {role} - {content[:50]}...")
    
    def obter_ultimas(self, n: int = 5) -> List[Dict[str, str]]:
        """Retorna as últimas n mensagens no formato para a API."""
        ultimas = self.mensagens[-n:]
        return [{"role": msg.role, "parts": [msg.content]} for msg in ultimas]
    
    def obter_todo_formato_api(self) -> List[Dict[str, str]]:
        """Retorna todo o histórico no formato da API Gemini."""
        return [{"role": msg.role, "parts": [msg.content]} for msg in self.mensagens]
    
    def registrar_afunilamento(self, pergunta: str, contexto_original: str) -> None:
        """Registra que uma pergunta de afunilamento foi feita, aguardando resposta."""
        self.pendencias_contexto["aguardando"] = True
        self.pendencias_contexto["pergunta_feita"] = pergunta
        self.pendencias_contexto["contexto_original"] = contexto_original
    
    def limpar_afunilamento(self) -> None:
        """Limpa o estado de afunilamento após uso."""
        self.pendencias_contexto.clear()

# ============================================================================
# GERENCIADOR DO CHATBOT
# ============================================================================

class ChatBotLiterario:
    """
    Chatbot especializado no mercado literário brasileiro utilizando Google Gemini.
    Implementa regras de negócio, verificação de fatos e indicação de obras.
    """
    
    def __init__(self, api_key: str, modelo: str = "gemini-2.5-flash"):
        """
        Inicializa o chatbot com a API key e configura o modelo.
        
        Args:
            api_key: Chave de API do Google AI Studio.
            modelo: Nome do modelo (padrão: gemini-2.5-flash).
        """
        self.api_key = api_key
        self.modelo_nome = modelo
        self.historico = HistoricoConversa()
        
        # Configura o cliente Gemini
        genai.configure(api_key=self.api_key)
        
        # Cria o modelo com as instruções sistêmicas
        self.modelo = genai.GenerativeModel(
            model_name=self.modelo_nome,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Inicializa o chat (mantém estado da conversa)
        self.chat = self.modelo.start_chat(history=[])
        
        logger.info(f"ChatBot inicializado com modelo {self.modelo_nome}")
    
    # ------------------------------------------------------------------------
    # Hooks e validações para forçar o comportamento correto
    # ------------------------------------------------------------------------
    
    def _hook_pre_processamento(self, mensagem_usuario: str) -> str:
        """
        Hook executado antes de enviar a mensagem ao modelo.
        Realiza validações e prepara o contexto.
        """
        # Verifica se há pendência de afunilamento (usuário respondendo pergunta anterior)
        if self.historico.pendencias_contexto.get("aguardando"):
            contexto_original = self.historico.pendencias_contexto.get("contexto_original", "")
            pergunta_feita = self.historico.pendencias_contexto.get("pergunta_feita", "")
            # Cria um prompt enriquecido com o contexto de afunilamento
            mensagem_enriquecida = (
                f"[CONTEXTO DE AFUNILAMENTO]\n"
                f"Mensagem original do usuário: {contexto_original}\n"
                f"Pergunta que você fez: {pergunta_feita}\n"
                f"Resposta do usuário: {mensagem_usuario}\n\n"
                f"Agora, com base nessas informações, responda adequadamente ao usuário."
            )
            self.historico.limpar_afunilamento()
            logger.info("Hook de afunilamento aplicado.")
            return mensagem_enriquecida
        
        # Se o usuário mandar uma mensagem muito curta ou vaga, o próprio modelo decidirá perguntar
        # Mas podemos adicionar um marcador para facilitar o afunilamento
        if len(mensagem_usuario.strip().split()) < 3:
            logger.info("Mensagem curta detectada - o modelo provavelmente fará pergunta de afunilamento.")
        
        return mensagem_usuario
    
    def _hook_pos_processamento(self, resposta: str, mensagem_original: str) -> str:
        """
        Hook executado após a resposta do modelo.
        Verifica se a resposta contém indicação de obra no formato correto.
        Se não, adiciona um lembrete (apenas em desenvolvimento, não para produção).
        """
        # Verifica se a resposta parece conter uma indicação de livro
        if " - " in resposta and ("sinopse" in resposta.lower() or "Sinopse" in resposta):
            # Formato parece ok, mas podemos validar mais
            pass
        elif "recomendo" in resposta.lower() or "sugiro" in resposta.lower():
            # Se há recomendação mas sem formato, adiciona aviso (opcional)
            logger.warning("Resposta com recomendação fora do formato padrão.")
        
        return resposta
    
    # ------------------------------------------------------------------------
    # Método principal de processamento
    # ------------------------------------------------------------------------
    
    def enviar_mensagem(self, mensagem_usuario: str) -> str:
        """
        Processa uma mensagem do usuário e retorna a resposta do chatbot.
        
        Args:
            mensagem_usuario: Texto enviado pelo usuário.
        
        Returns:
            Resposta gerada pelo modelo Gemini.
        """
        if not mensagem_usuario or not mensagem_usuario.strip():
            return "Por favor, envie uma mensagem válida sobre o mercado literário brasileiro."
        
        # Adiciona ao histórico (role user)
        self.historico.adicionar("user", mensagem_usuario)
        
        # Aplica hook de pré-processamento
        prompt_processado = self._hook_pre_processamento(mensagem_usuario)
        
        try:
            # Envia a mensagem para o chat Gemini (mantém histórico internamente)
            # Mas também passamos o histórico completo explicitamente para garantir contexto
            # O objeto self.chat já mantém histórico, mas vamos forçar usando send_message
            resposta = self.chat.send_message(prompt_processado)
            resposta_texto = resposta.text
            
            # Aplica hook de pós-processamento
            resposta_texto = self._hook_pos_processamento(resposta_texto, mensagem_usuario)
            
            # Adiciona resposta ao histórico local
            self.historico.adicionar("assistant", resposta_texto)
            
            return resposta_texto
            
        except Exception as e:
            logger.error(f"Erro ao comunicar com a API Gemini: {str(e)}")
            # Fallback amigável
            return ("Ocorreu um erro ao processar sua solicitação. "
                    "Verifique sua chave de API e conexão com a internet (necessária para acessar o Gemini). "
                    "Lembre-se: o chatbot depende da API do Google, embora o conhecimento do modelo seja offline.")
    
    def resetar_conversa(self) -> None:
        """Reinicia o histórico da conversa e cria um novo chat."""
        self.historico = HistoricoConversa()
        self.chat = self.modelo.start_chat(history=[])
        logger.info("Conversa resetada.")
    
    def obter_historico_formatado(self) -> str:
        """Retorna o histórico da conversa em formato legível."""
        linhas = []
        for msg in self.historico.mensagens:
            role = "Você" if msg.role == "user" else "ChatBot"
            linhas.append(f"{role}: {msg.content}")
        return "\n".join(linhas)

# ============================================================================
# FUNÇÃO PRINCIPAL PARA EXECUÇÃO DO CHATBOT (INTERFACE DE LINHA DE COMANDO)
# ============================================================================

def main():
    """
    Função principal que inicia o chatbot e gerencia a interação via terminal.
    O usuário deve fornecer a chave da API do Google Gemini.
    """
    print("=" * 70)
    print("📚 ChatBot do Mercado Literário Brasileiro 📚")
    print("=" * 70)
    print("Especialista em rankings, autores, gêneros e tendências do Brasil.")
    print("Digite 'sair' para encerrar, 'reset' para reiniciar a conversa, 'historico' para ver o histórico.")
    print("-" * 70)
    
    # Obtém a chave da API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n⚠️  Variável de ambiente GEMINI_API_KEY não encontrada.")
        api_key = input("Digite sua chave de API do Google Gemini: ").strip()
        if not api_key:
            print("Erro: Chave de API necessária. Encerrando.")
            return
    
    try:
        bot = ChatBotLiterario(api_key=api_key, modelo="gemini-2.5-flash")
        print("\n✅ ChatBot pronto! Faça sua pergunta sobre o mercado literário brasileiro.\n")
        
        while True:
            usuario = input("\nVocê: ").strip()
            if usuario.lower() in ["sair", "exit", "quit"]:
                print("Encerrando o chat. Até logo!")
                break
            elif usuario.lower() == "reset":
                bot.resetar_conversa()
                print("Conversa reiniciada.")
                continue
            elif usuario.lower() == "historico":
                print("\n--- Histórico da Conversa ---")
                print(bot.obter_historico_formatado())
                print("-------------------------------")
                continue
            
            resposta = bot.enviar_mensagem(usuario)
            print(f"\nChatBot: {resposta}")
            
    except KeyboardInterrupt:
        print("\n\nChat interrompido pelo usuário.")
    except Exception as e:
        logger.exception(f"Erro fatal: {e}")
        print(f"Ocorreu um erro inesperado: {e}")

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()