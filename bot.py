import sqlite3, os
from datetime import datetime
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

ADMIN_ID = 8449568289
TOKEN = "8954684493:AAHovhLYqZNipQ_krxrs0HtzxGNgzXYQn74"
CHAVE_PIX = "vittorteccell@gmail.com"

def init_db():
    conn = sqlite3.connect("vittorteccell.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            cliente TEXT,
            whatsapp TEXT,
            marca TEXT,
            modelo TEXT,
            servico_realizado TEXT,
            valor_total REAL,
            adiantamento REAL,
            restante REAL,
            status TEXT,
            pagamento_entrada TEXT,
            pagamento_final TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()
user_states = {}
user_data_temp = {}

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id): return
    conn = sqlite3.connect("vittorteccell.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor_total), SUM(adiantamento), SUM(restante), COUNT(*) FROM servicos")
    res = cursor.fetchone()
    conn.close()
    total, adiant, rest, qtd = res[0] or 0.0, res[1] or 0.0, res[2] or 0.0, res[3] or 0
    texto = f"🛠 *VITTORTECCELL* 🛠\n*Controle de OS Profissional*\n\n📊 Faturamento Total: R$ {total:.2f}\n📥 Adiantamentos: R$ {adiant:.2f}\n⏳ A Receber: R$ {rest:.2f}\n📋 Total OS: {qtd}\n\n🔑 PIX: `{CHAVE_PIX}`"
    teclado = [
        [InlineKeyboardButton("➕ 1. Nova OS", callback_data="novo_servico"), InlineKeyboardButton("📁 Arquivo OS", callback_data="listar_servicos")],
        [InlineKeyboardButton("📲 2. Aparelho Pronto", callback_data="passo_pronto"), InlineKeyboardButton("🏁 3. Concluir & Garantia", callback_data="passo_concluir")],
        [InlineKeyboardButton("🔍 Buscar Cliente", callback_data="buscar_menu"), InlineKeyboardButton("📊 Relatórios de Caixa", callback_data="relatorios")],
        [InlineKeyboardButton("💾 Backup", callback_data="backup"), InlineKeyboardButton("❓ Ajuda", callback_data="ajuda")]
    ]
    if update.callback_query:
        await update.callback_query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(teclado), parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(teclado), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_admin(user_id): return
    data = query.data

    if data == "menu_principal":
        await start(update, context)
    elif data == "novo_servico":
        user_states[user_id] = "aguardando_cliente"
        user_data_temp[user_id] = {"data": datetime.now().strftime("%d/%m/%Y")}
        await query.message.reply_text("📅 *PASSO 1: Abertura de OS*\n\n👤 Digite o **Nome do cliente**:", parse_mode="Markdown")
    elif data.startswith("marca_"):
        marca = data.replace("marca_", "")
        user_data_temp[user_id]["marca"] = marca
        user_states[user_id] = "aguardando_modelo"
        await query.message.reply_text(f"📱 Marca: **{marca}**\n\nAgora digite o **Modelo do aparelho** (ex: A07):", parse_mode="Markdown")
    elif data.startswith("pag_ent_"):
        pag = data.replace("pag_ent_", "")
        user_data_temp[user_id]["pag_entrada"] = pag
        user_states[user_id] = "aguardando_servico"
        await query.message.reply_text(f"💳 Forma de Entrada: **{pag}**\n\n🛠️ Digite agora o **Serviço realizado** (ex: Troca de tela):", parse_mode="Markdown")
    elif data.startswith("pag_fin_"):
        partes = data.replace("pag_fin_", "").rsplit("_", 1)
        pag_final = partes[0]
        s_id = int("".join(filter(str.isdigit, partes[1])))
        
        conn = sqlite3.connect("vittorteccell.db")
        c = conn.cursor()
        c.execute("UPDATE servicos SET status = 'CONCLUÍDO', pagamento_final = ? WHERE id = ?", (pag_final, s_id))
        c.execute("SELECT id, cliente, whatsapp, marca, modelo, servico_realizado, valor_total, data, adiantamento, restante FROM servicos WHERE id = ?", (s_id,))
        s = c.fetchone()
        conn.close()
        user_states.pop(user_id, None)

        texto_zap = (
            f"🛠 *VITTORTECCELL - SERVIÇO CONCLUÍDO*\n\n"
            f"📅 Data: {s[7]}\n"
            f"📋 OS {s[0]}\n"
            f"👤 Cliente: {s[1]}\n"
            f"📱 Aparelho: {s[3]} {s[4]}\n"
            f"🛠 Serviço: {s[5]}\n"
            f"💵 Restante pago em: {pag_final}\n"
            f"💰 Valor Total: R$ {s[6]:.2f}\n\n"
            f"✅ Serviço concluído e testado com sucesso!\n\n"
            f"🛡 *TERMO DE GARANTIA (90 DIAS)*\n"
            f"• Cobertura: 90 dias de garantia legal contra defeitos na peça aplicada ou na mão de obra do serviço executado.\n"
            f"• Exclusões (Perda da Garantia):\n"
            f"  ❌ Quedas, impactos, trincas ou telas quebradas após a entrega.\n"
            f"  ❌ Contato com líquidos, água, umidade ou oxidação interna.\n"
            f"  ❌ Mau uso, pressão excessiva ou tentativa de reparo por terceiros.\n"
            f"  ❌ Violação, rasura ou remoção dos selos e etiquetas de garantia da assistência.\n\n"
            f"Obrigado pela preferência e confiança em nosso trabalho! 🙏"
        )
        
        botoes = []
        if s[2] and s[2].strip().lower() not in ["não", "nao", ""]:
            num_zap = "".join(filter(str.isdigit, s[2]))
            if len(num_zap) >= 8:
                link_zap = f"https://wa.me/55{num_zap}?text={quote(texto_zap)}"
                botoes.append([InlineKeyboardButton("💬 Enviar Comprovativo ao Cliente", url=link_zap)])
        
        botoes.append([InlineKeyboardButton("⬅️ Voltar ao Menu Principal", callback_data="menu_principal")])

        resp = f"🏁 *ENCERRAMENTO E GARANTIA - OS {s_id}* (Passo 3)\n\n" + texto_zap
        await query.message.edit_text(resp, reply_markup=InlineKeyboardMarkup(botoes), parse_mode="Markdown")
    elif data == "listar_servicos":
        conn = sqlite3.connect("vittorteccell.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, cliente, whatsapp, marca, modelo, servico_realizado, valor_total, adiantamento, restante, status, data FROM servicos ORDER BY id DESC LIMIT 15")
        servicos = cursor.fetchall()
        conn.close()
        texto = "📁 *ÚLTIMAS ORDENS DE SERVIÇO:*\n\n" if servicos else "📭 Nenhuma OS registrada."
        for s in servicos:
            texto += f"🔹 *OS {s[0]}* ({s[10]}) | {s[1]}\n📱 {s[3]} {s[4]} - {s[5]}\n💵 Total: R$ {s[6]:.2f} | Rest: R$ {s[8]:.2f}\n📌 Status: *{s[9]}*\n-------------------\n"
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu_principal")]]), parse_mode="Markdown")
    elif data == "passo_pronto":
        user_states[user_id] = "aguardando_pronto_id"
        await query.message.reply_text("📲 Digite o **número da OS** que já está pronta (Passo 2):")
    elif data == "passo_concluir":
        user_states[user_id] = "aguardando_concluir_id"
        await query.message.reply_text("🏁 Digite o **número da OS** para concluir (Passo 3):")
    elif data == "buscar_menu":
        user_states[user_id] = "aguardando_termo_busca"
        await query.message.reply_text("🔍 Digite o **Nome do cliente** ou **Modelo** que deseja procurar:")
    elif data == "relatorios":
        hoje = datetime.now().strftime("%d/%m/%Y")
        mes_atual = datetime.now().strftime("/%m/%Y")
        conn = sqlite3.connect("vittorteccell.db")
        c = conn.cursor()
        c.execute("SELECT SUM(valor_total) FROM servicos WHERE data = ?", (hoje,))
        f_hoje = c.fetchone()[0] or 0.0
        c.execute("SELECT SUM(valor_total) FROM servicos WHERE data LIKE ?", ('%' + mes_atual,))
        f_mes = c.fetchone()[0] or 0.0
        conn.close()
        texto = f"📊 *RELATÓRIOS DE CAIXA - VITTORTECCELL*\n\n📅 Faturamento Hoje ({hoje}): **R$ {f_hoje:.2f}**\n📆 Faturamento deste Mês: **R$ {f_mes:.2f}**"
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu_principal")]]), parse_mode="Markdown")
    elif data == "backup":
        if os.path.exists("vittorteccell.db"):
            with open("vittorteccell.db", "rb") as f:
                await context.bot.send_document(chat_id=user_id, document=f, filename="backup_vittorteccell.db", caption="💾 Backup!")
            await query.message.edit_text("✅ Backup enviado!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu_principal")]]))
    elif data == "ajuda":
        await query.message.reply_text("📖 *Ajuda - Vittorteccell*\n1. **Nova OS**: Regista com escolha de Pix ou Dinheiro.\n2. **Aparelho Pronto**: Avisa que está pronto e cobra o restante.\n3. **Concluir**: Envia o recibo, forma de pagamento e Termo de Garantia de 90 dias.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu_principal")]]), parse_mode="Markdown")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id): return
    text = update.message.text
    state = user_states.get(user_id)

    if state == "aguardando_cliente":
        user_data_temp[user_id]["cliente"] = text
        user_states[user_id] = "aguardando_whatsapp"
        await update.message.reply_text("💬 Digite o **WhatsApp** com DDD (ou digite 'não'):")
    elif state == "aguardando_whatsapp":
        user_data_temp[user_id]["whatsapp"] = text.strip()
        user_states[user_id] = "aguardando_marca"
        marcas = [[InlineKeyboardButton("Xiaomi", callback_data="marca_Xiaomi"), InlineKeyboardButton("Samsung", callback_data="marca_Samsung")],
                  [InlineKeyboardButton("Motorola", callback_data="marca_Motorola"), InlineKeyboardButton("Apple", callback_data="marca_Apple")],
                  [InlineKeyboardButton("Outra", callback_data="marca_Outra")]]
        await update.message.reply_text("🏷️ Selecione a **Marca**:", reply_markup=InlineKeyboardMarkup(marcas))
    elif state == "aguardando_modelo":
        user_data_temp[user_id]["modelo"] = text
        user_states[user_id] = "aguardando_pag_entrada"
        pag_menu = [[InlineKeyboardButton("💳 PIX (Entrada)", callback_data="pag_ent_PIX"), InlineKeyboardButton("💵 Dinheiro (Entrada)", callback_data="pag_ent_Dinheiro")]]
        await update.message.reply_text("💰 Como foi paga a **Entrada (Adiantamento)**?", reply_markup=InlineKeyboardMarkup(pag_menu))
    elif state == "aguardando_servico":
        user_data_temp[user_id]["servico"] = text
        user_states[user_id] = "aguardando_valor_total"
        await update.message.reply_text("💵 Digite o **Valor total do serviço (R$)** (Ex: 150.00):")
    elif state == "aguardando_valor_total":
        try:
            total = float(text.replace(",", "."))
            d = user_data_temp[user_id]
            adiantamento = total / 2.0
            restante = total - adiantamento
            status = "AGUARDANDO ADIANTAMENTO"

            conn = sqlite3.connect("vittorteccell.db")
            c = conn.cursor()
            c.execute("INSERT INTO servicos (data, cliente, whatsapp, marca, modelo, servico_realizado, valor_total, adiantamento, restante, status, pagamento_entrada) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (d["data"], d["cliente"], d["whatsapp"], d["marca"], d["modelo"], d["servico"], total, adiantamento, restante, status, d["pag_entrada"]))
            s_id = c.lastrowid
            conn.commit()
            conn.close()

            user_states.pop(user_id, None)
            user_data_temp.pop(user_id, None)

            botoes = []
            if d['whatsapp'] and d['whatsapp'].strip().lower() not in ["não", "nao", ""]:
                num_zap = "".join(filter(str.isdigit, d['whatsapp']))
                if len(num_zap) >= 8:
                    msg_os = (
                        f"🛠 *VITTORTECCELL - ORDEM DE SERVIÇO*\n\n"
                        f"📅 Data: {d['data']}\n"
                        f"📋 OS {s_id}\n"
                        f"👤 Cliente: {d['cliente']}\n"
                        f"📱 Aparelho: {d['marca']} {d['modelo']}\n"
                        f"🛠 Serviço: {d['servico']}\n\n"
                        f"💵 Valor Total: R$ {total:.2f}\n"
                        f"📥 Adiantamento ({d['pag_entrada']}): R$ {adiantamento:.2f}\n"
                        f"🔑 Chave PIX: {CHAVE_PIX}\n\n"
                        f"Obrigado pela preferência! 🙏"
                    )
                    link_os = f"https://wa.me/55{num_zap}?text={quote(msg_os)}"
                    botoes.append([InlineKeyboardButton("💬 Enviar OS ao Cliente", url=link_os)])
            
            botoes.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu_principal")])
            resp = f"✅ *OS {s_id} CRIADA (Passo 1)*\n\n👤 Cliente: {d['cliente']}\n📱 Aparelho: {d['marca']} {d['modelo']}\n💵 Total: R$ {total:.2f} | Adiantamento ({d['pag_entrada']}): **R$ {adiantamento:.2f}**"
            await update.message.reply_text(resp, reply_markup=InlineKeyboardMarkup(botoes), parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Use números (Ex: 150.00):")
    elif state == "aguardando_pronto_id":
        try:
            s_id = int(text)
            conn = sqlite3.connect("vittorteccell.db")
            c = conn.cursor()
            c.execute("SELECT id, cliente, whatsapp, marca, modelo, restante FROM servicos WHERE id = ?", (s_id,))
            s = c.fetchone()
            conn.close()
            if not s:
                await update.message.reply_text("❌ OS não encontrada:")
                return
            conn = sqlite3.connect("vittorteccell.db")
            c = conn.cursor()
            c.execute("UPDATE servicos SET status = 'PRONTO PARA ENTREGA' WHERE id = ?", (s_id,))
            conn.commit()
            conn.close()
            user_states.pop(user_id, None)

            botoes = []
            if s[2] and s[2].strip().lower() not in ["não", "nao", ""]:
                num_zap = "".join(filter(str.isdigit, s[2]))
                if len(num_zap) >= 8:
                    msg_pronto = (
                        f"🛠 *VITTORTECCELL - APARELHO PRONTO*\n\n"
                        f"📋 OS {s_id}\n"
                        f"👤 Cliente: {s[1]}\n"
                        f"📱 Aparelho: {s[3]} {s[4]}\n\n"
                        f"✨ O seu aparelho já está pronto!\n"
                        f"⏳ Valor Restante: R$ {s[5]:.2f}\n"
                        f"🔑 Chave PIX: {CHAVE_PIX}\n\n"
                        f"Pode efetuar o pagamento do restante para a retirada! 🙏"
                    )
                    link_pronto = f"https://wa.me/55{num_zap}?text={quote(msg_pronto)}"
                    botoes.append([InlineKeyboardButton("💬 Enviar Aviso de Aparelho Pronto", url=link_pronto)])
            
            botoes.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu_principal")])
            resp = f"📲 *APARELHO PRONTO - OS {s_id}* (Passo 2)\nCliente: {s[1]}\nRestante a cobrar: **R$ {s[5]:.2f}**"
            await update.message.reply_text(resp, reply_markup=InlineKeyboardMarkup(botoes), parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Número inválido:")
    elif state == "aguardando_concluir_id":
        try:
            s_id = int(text)
            conn = sqlite3.connect("vittorteccell.db")
            c = conn.cursor()
            c.execute("SELECT id, cliente FROM servicos WHERE id = ?", (s_id,))
            s = c.fetchone()
            conn.close()
            if not s:
                await update.message.reply_text("❌ OS não encontrada:")
                return
            
            user_states.pop(user_id, None)

            pag_menu = [[InlineKeyboardButton("💳 PIX (Restante)", callback_data=f"pag_fin_PIX_{s_id}"), InlineKeyboardButton("💵 Dinheiro (Restante)", callback_data=f"pag_fin_Dinheiro_{s_id}")]]
            await update.message.reply_text(f"🏁 *OS {s_id} - Conclusão*\nComo foi pago o **Valor Restante**?", reply_markup=InlineKeyboardMarkup(pag_menu), parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Número inválido:")
    elif state == "aguardando_termo_busca":
        termo = f"%{text}%"
        conn = sqlite3.connect("vittorteccell.db")
        c = conn.cursor()
        c.execute("SELECT id, cliente, marca, modelo, servico_realizado, valor_total, status, data FROM servicos WHERE cliente LIKE ? OR modelo LIKE ? OR marca LIKE ? ORDER BY id DESC", (termo, termo, termo))
        resultados = c.fetchall()
        conn.close()
        user_states.pop(user_id, None)

        texto = f"🔍 *RESULTADOS DA BUSCA ('{text}'):*\n\n" if resultados else f"❌ Nenhum resultado encontrado para '{text}'."
        for r in resultados:
            texto += f"🔹 *OS {r[0]}* ({r[7]}) | {r[1]}\n📱 {r[2]} {r[3]} - {r[4]}\n💵 R$ {r[5]:.2f} | Status: *{r[6]}*\n-------------------\n"
        await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu_principal")]]), parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).connect_timeout(60).read_timeout(60).write_timeout(60).pool_timeout(60).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    print("🤖 Bot Vittorteccell em nuvem a rodar perfeitamente!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
