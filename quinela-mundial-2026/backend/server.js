// backend/server.js
require('dotenv').config();
const express = require('express');
const archiver = require('archiver');
const nodemailer = require('nodemailer');
const crypto = require('crypto');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Configuración de Email (desde .env o variables)
const EMAIL_CONFIG = {
  service: process.env.EMAIL_SERVICE || 'gmail',
  user: process.env.EMAIL_USER,
  pass: process.env.EMAIL_PASS,
  recipients: (process.env.RECIPIENTS || 'yoany.fuentes@etecsa.cu,jorge.diaz@etecsa.cu').split(',')
};

// 🔐 Función para crear ZIP encriptado con AES-256
async function createEncryptedZip(data, userName, password) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    const archive = archiver('zip', { 
      zlib: { level: 9 },
      encryptionMethod: 'aes256',
      encryptionKey: password 
    });
    
    archive.on('data', chunk => chunks.push(chunk));
    archive.on('end', () => resolve(Buffer.concat(chunks)));
    archive.on('error', reject);
    
    // Agregar archivo TXT con las predicciones
    const content = generateTXTContent(data);
    archive.append(content, { name: `${userName}_Quinela2026.txt` });
    
    archive.finalize();
  });
}

// 📝 Generar contenido TXT (mismo formato que tu frontend)
function generateTXTContent(data) {
  let t = `🌍 BOLETA PREDICTIVA - MUNDIAL FIFA 2026\n`;
  t += `══════════════════════════════\n`;
  t += `👤 ${data.userName}\n📅 ${data.date}\n🕐 ${new Date().toLocaleString('es-ES')}\n\n`;
  t += `📊 FASE DE GRUPOS\n─────────────────\n`;
  
  const GROUPS = ['A','B','C','D','E','F','G','H','I','J','K','L'];
  GROUPS.forEach(g => {
    t+=`\n🔹 Grupo ${g}:\n`;
    for(let i=1;i<=6;i++) if(data.groups?.[`${g}${i}`]) t+=`   P${i}: ${data.groups[`${g}${i}`]}\n`;
    if(data.qualified?.[g]) t+=`   Clas: 1°:${data.qualified[g].first||'__'} 2°:${data.qualified[g].second||'__'} 3°:${data.qualified[g].third||'__'}\n`;
  });
  
  t+=`\n🏆 ELIMINATORIAS\n─────────────────\n`;
  ['R','OF','CF','SF'].forEach(pf => {
    const cnt = pf==='R'?16:pf==='OF'?8:pf==='CF'?4:2;
    for(let i=1;i<=cnt;i++) if(data.knockout?.[`${pf}${i}`]) {
      const k=data.knockout[`${pf}${i}`]; t+=`   ${pf}-${i}: ${k.p||'__'}${k.pen?' ★':''}\n`;
    }
  });
  if(data.knockout?.['3RD']) { const k=data.knockout['3RD']; t+=`   🥉: ${k.p||'__'}${k.pen?' ★':''}\n`; }
  if(data.knockout?.['FINAL']) { const k=data.knockout['FINAL']; t+=`   🥇: ${k.p||'__'}${k.pen?' ★':''}\n`; }
  
  t+=`\n🏅 PREMIOS\n─────────────────\n`;
  t+=`⚽ Goleador: ${data.awards?.ts||'__'} (${data.awards?.tsg||'__'}g)\n`;
  t+=`🎯 Asist: ${data.awards?.ta||'__'}\n🌟 Balón Oro: ${data.awards?.gb||'__'}\n`;
  t+=`\n══════════════════════════════\n✅ Quinela FIFA 2026™\n👨‍💻 Ing. Yoany Fuentes Ruíz`;
  return t;
}

// 📧 Función para enviar email con adjunto
async function sendEmail({ to, subject, message, attachment, fileName }) {
  const transporter = nodemailer.createTransport({
    service: EMAIL_CONFIG.service,
    auth: { user: EMAIL_CONFIG.user, pass: EMAIL_CONFIG.pass }
  });
  
  const mailOptions = {
    from: `"Quinela Mundial 2026" <${EMAIL_CONFIG.user}>`,
    to: to.join(','),
    subject: subject,
    text: message,
    attachments: [{ filename: fileName, content: attachment }]
  };
  
  return await transporter.sendMail(mailOptions);
}

// 🌐 Endpoint principal: recibir predicción y enviar ZIP encriptado
app.post('/api/submit', async (req, res) => {
  try {
    const { userName, predictions, password = 'Ok12345*' } = req.body;
    
    if(!userName || !predictions) {
      return res.status(400).json({ error: 'Faltan datos requeridos' });
    }
    
    // 1. Crear ZIP encriptado
    const zipBuffer = await createEncryptedZip(predictions, userName, password);
    const fileName = `${userName.replace(/[^a-z0-9]/gi,'_')}_Quinela2026.zip`;
    
    // 2. Enviar email
    await sendEmail({
      to: EMAIL_CONFIG.recipients,
      subject: `🌍 Quinela Mundial 2026 - ${userName}`,
      message: `Adjunto predicciones de ${userName} para el Mundial FIFA 2026.\n\nContraseña del ZIP: ${password}\n\nSaludos,\nSistema Quinela - Ing. Yoany Fuentes Ruíz`,
      attachment: zipBuffer,
      fileName: fileName
    });
    
    // 3. Respuesta exitosa
    res.json({ 
      success: true, 
      message: 'Predicción enviada correctamente',
      fileName: fileName 
    });
    
  } catch(err) {
    console.error('Error en /api/submit:', err);
    res.status(500).json({ error: 'Error interno del servidor', details: err.message });
  }
});

// 📊 Endpoint para recibir ranking y guardar en Google Sheets (opcional)
app.post('/api/ranking', async (req, res) => {
  try {
    const { rankingData } = req.body;
    // Aquí podrías integrar con Google Sheets API si lo necesitas
    console.log('Ranking recibido:', rankingData?.length || 0, 'participantes');
    res.json({ success: true, message: 'Ranking procesado' });
  } catch(err) {
    res.status(500).json({ error: err.message });
  }
});

// 🏠 Endpoint para servir el frontend (opcional)
app.use(express.static(path.join(__dirname, '../frontend')));
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// 🚀 Iniciar servidor
app.listen(PORT, () => {
  console.log(`✅ Servidor Quinela corriendo en http://localhost:${PORT}`);
  console.log(`📧 Emails configurados para: ${EMAIL_CONFIG.recipients.join(', ')}`);
});
