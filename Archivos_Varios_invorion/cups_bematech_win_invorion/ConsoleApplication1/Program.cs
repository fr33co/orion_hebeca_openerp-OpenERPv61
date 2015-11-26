using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using FiscalPrinterBematech;
using System.IO;

namespace ConsoleApplication1
{
    class Program
    {
        static void Main(string[] args)
        {
            int IRetorno;
            IRetorno = BemaFI32.Bematech_FI_AbrePuertaSerial();
            BemaFI32.Analisa_iRetorno(IRetorno);
            BemaFI32.Analisa_RetornoImpresora();
            
            //Aqui Comienzo Funcion de Impresion
            //string ruta = "";
            string Hora, Min, Seg, Dia, Mes, Anio;
            DateTime d = DateTime.Now;

            Hora = d.Hour.ToString();
            Min = d.Minute.ToString();
            Seg = d.Second.ToString();
            Dia = d.Day.ToString();
            Mes = d.Month.ToString();
            Anio = d.Month.ToString();

            string[] files = Directory.GetFiles("C:/cygwin/home/Equipo", "*.FC");
            foreach (string file in files)
            {
                Console.WriteLine(files);
                Console.WriteLine(file);
                string pago;
                pago = "";

                StreamReader leer = new StreamReader(file);
                string linea = "";
                string[] lineas;
                //ArrayList arrText = new ArrayList();
                while (linea != null)
                {
                    linea = leer.ReadLine();

                    if (linea != null)
                    {
                        lineas = linea.Split(';');
                        //Inicio de Tratado de Linea Cabecera
                        if (lineas[0] == "out_invoice")
                        {
                            Console.WriteLine("Imprime Factura");
                            Console.WriteLine(lineas[0]);
                            Console.WriteLine(lineas[1]);
                            Console.WriteLine(lineas[2]);
                            Console.WriteLine(lineas[3]);
                            pago = lineas[3];
                            IRetorno = BemaFI32.Bematech_FI_AbreComprobanteDeVenta(lineas[2], lineas[1]);
                            BemaFI32.Analisa_iRetorno(IRetorno);
                            BemaFI32.Analisa_RetornoImpresora();
                        }
                        if (lineas[0] == "out_refund")
                        {
                            Console.WriteLine("Imprime Nota de Credito");
                            Console.WriteLine(lineas[0]);
                            Console.WriteLine(lineas[1]);
                            Console.WriteLine(lineas[2]);
                            IRetorno = BemaFI32.Bematech_FI_AbreNotaDeCredito(lineas[1], "1FC2308276", lineas[2], Dia, Mes, Anio, Hora, Min, Seg, "123456", "Gracias, Vuelva Siempre");
                            BemaFI32.Analisa_iRetorno(IRetorno);
                            BemaFI32.Analisa_RetornoImpresora();
                        }
                        //Fin de Tratado de Linea Cabecera
                        if (lineas.Length > 4)
                        {
                            //Inicio de Tratado de Lineas Hijas
                             Console.WriteLine(lineas[0]);
                             Console.WriteLine(lineas[1]);
                             Console.WriteLine(lineas[2]);
                             Console.WriteLine(lineas[3]);
                             Console.WriteLine(lineas[4]);
                             Console.WriteLine(lineas[5]);
                             Console.WriteLine(lineas[6]);
                             Console.WriteLine(lineas[7]);

                            IRetorno = BemaFI32.Bematech_FI_VendeArticulo(lineas[0], lineas[1], lineas[2], lineas[3], lineas[4].Replace(".", ","), 2, lineas[5], lineas[6], lineas[7]);
                            BemaFI32.Analisa_iRetorno(IRetorno);
                            BemaFI32.Analisa_RetornoImpresora();
                        }
                        //Fin de Tratado de Lineas Hijas
                    }
                }
                IRetorno = BemaFI32.Bematech_FI_CierraCupon("Efectivo", "A", "%", "0000", pago, "Vuelva Siempre!");
                BemaFI32.Analisa_iRetorno(IRetorno);
                BemaFI32.Analisa_RetornoImpresora();
                leer.Close();
                Console.WriteLine(file);
                if (linea == null)
                {
                    System.IO.File.Delete(file);
                }
            }// Fin For Each
            Console.WriteLine("Impresion Realizada");
            IRetorno = BemaFI32.Bematech_FI_CierraPuertaSerial();
            BemaFI32.Analisa_iRetorno(IRetorno);
        }
    }
}
