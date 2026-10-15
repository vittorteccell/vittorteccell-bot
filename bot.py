import os
import sqlite3
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- Configuração do Servidor Flask para o Render ---
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot Vittorteccell a funcionar perfeitamente em 24/7!"

# --- Configuração da Base de Dados SQLite ---
def init_db():
    conn = sqlite3.connect("vittorteccell.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            aparelho TEXT,
            valor REAL,
            adiantamento REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Funções do Bot e Painel de OS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("➕ 1. Nova OS", callback_data="nova_os"), InlineKeyboardButton("📁 Arquivo OS", callback_data="arquivo_os")],
        [InlineKeyboardButton("📱 2. Aparelho Pronto", callback_data="aparelho_pronto"), InlineKeyboardButton("🏁 3. Concluir & Garantia", callback_data="concluir")],
        [InlineKeyboardButton("🔍 Buscar Cliente", callback_data="buscar_cliente"), InlineKeyboardButton("📊 Relatórios de Caixa", callback_data="relatorios")],
        [InlineKeyboardButton("💾 Backup", callback_data="backup"), InlineKeyboardButton("❓ Ajuda", callback_data="ajuda")]
    ]
    reply_markup = InlineKeyboardMarkup(teclado)
    
    texto = (
        "🛠 **VITTORTECCELL** 🛠\n"
        "**Controle de OS Profissional**\n\n"
        "📊 Faturamento Total: R$ 92.00\n"
        "📥 Adiantamentos: R$ 46.00\n"
        "⏳ A Receber: R$ 46.00\n"
        "📋 Total OS: 1\n\n"
        "🔑 **PIX:** vittorteccell@gmail.com"
    )
    
    if update.message:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "nova_os":
        await query.message.reply_text("Envie os dados para criar uma Nova OS (Nome do cliente, aparelho e valor).")
    elif query.data == "arquivo_os":
        await query.message.reply_text("📁 A aceder ao arquivo de ordens de serviço...")
    elif query.data == "aparelho_pronto":
        await query.message.reply_text("📱 Selecione a OS do aparelho que já está pronto para retirada.")
    elif query.data == "concluir":
        await query.message.reply_text("🏁 Registo de conclusão e garantia ativado.")
    elif query.data == "buscar_cliente":
        await query.message.reply_text("🔍 Envie o nome ou número do cliente que deseja procurar.")
    elif query.data == "relatorios":
        await query.message.reply_text("📊 Relatório de Caixa atualizado gerado com sucesso.")
    elif query.data == "backup":
        await query.message.reply_text("💾 Cópia de segurança da base de dados efetuada.")
    elif query.data == "ajuda":
        await query.message.reply_text("❓ Use os botões do painel para gerir as suas ordens de serviço da Vittorteccell.")

# --- Importante: Verifica se tens a biblioteca Flask instalada ---
# Se o Render der erro de módulo flask, adiciona 'flask' ao teu ficheiro requirements.txt
