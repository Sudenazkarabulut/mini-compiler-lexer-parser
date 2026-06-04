import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from lexer import tokenize
from parser import Parser
import json

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'r') as file:
            text_input.delete("1.0", tk.END)
            text_input.insert(tk.END, file.read())

def run_compiler():
    # get code
    source_code = text_input.get("1.0", tk.END)
    
    # Pass 1: lexer
    tokens, lex_errors = tokenize(source_code)
    
    # Clear Table
    for item in tree.get_children():
        tree.delete(item)
    for t in tokens:
        tree.insert('', tk.END, values=(t['line'], t['value'], t['type']))

    # Pass 2: Parser & Semantic Analysis
    parser = Parser(tokens)
    parser.parse()

    # fill symbol table
    for item in sym_tree.get_children(): 
        sym_tree.delete(item)
    for var, info in parser.symbol_table.items():
        # FIX: Changed to info.get() to avoid the dictionary error
        sym_tree.insert('', tk.END, values=(var, info['type'], "Global", info.get('address', '0x00')))

    # Display AST 
    ast_display.config(state='normal')
    ast_display.delete('1.0', tk.END)
    ast_display.insert(tk.END, json.dumps(parser.ast, indent=4))
    ast_display.config(state='disabled')
    
    all_errors = lex_errors + parser.errors

    # Display Errors 
    error_display.config(state='normal') 
    error_display.delete('1.0', tk.END) 
    if all_errors:
        for err in all_errors:
            error_display.insert(tk.END, err + "\n", "error_tag")
    else:
        error_display.insert(tk.END, "Compilation Successful! No errors found.", "success_tag")
    error_display.config(state='disabled')


# --- UI Setup ---
root = tk.Tk()
root.title("Compiler")
root.geometry("1100x800") # Made slightly wider for the 3 columns

# 1. Main Vertical Paned Window
main_pane = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4)
main_pane.pack(fill=tk.BOTH, expand=True)

# --- TOP SECTION: Code Input ---
top_frame = tk.Frame(main_pane)
tk.Label(top_frame, text="Code:").pack(anchor="w", padx=10)
text_input = tk.Text(top_frame, height=10)
text_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
main_pane.add(top_frame)

# --- MIDDLE SECTION: Run Button and Tables ---
mid_frame = tk.Frame(main_pane)

# buttons Row
btn_frame = tk.Frame(mid_frame)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="Run Compiler", command=run_compiler, bg="green", fg="white", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Upload File", command=open_file).pack(side=tk.LEFT, padx=5)

# side-by-side tables
table_pane = tk.PanedWindow(mid_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
table_pane.pack(fill=tk.BOTH, expand=True, padx=10)

# Token Table
token_frame = tk.Frame(table_pane)
tk.Label(token_frame, text="Tokens:").pack()
tree = ttk.Treeview(token_frame, columns=('L', 'V', 'T'), show='headings')
tree.heading('L', text='Line'); tree.heading('V', text='Value'); tree.heading('T', text='Type')
tree.column('L', width=50)
tree.pack(fill=tk.BOTH, expand=True)
table_pane.add(token_frame)

# Symbol Table
symbol_frame = tk.Frame(table_pane)
tk.Label(symbol_frame, text="Symbol Table:").pack()
sym_tree = ttk.Treeview(symbol_frame, columns=('N', 'T','S', 'A'), show='headings')
sym_tree.heading('N', text='Name'); 
sym_tree.heading('T', text='Type'); 
sym_tree.heading('S', text='Scope'); 
sym_tree.heading('A', text='Address')
sym_tree.column('N', width=80); 
sym_tree.column('T', width=80); 
sym_tree.column('S', width=80); 
sym_tree.column('A', width=80)
sym_tree.pack(fill=tk.BOTH, expand=True)
table_pane.add(symbol_frame)

# AST Frame
ast_frame = tk.Frame(table_pane)
tk.Label(ast_frame, text="Abstract Syntax Tree (AST):").pack()
ast_display = tk.Text(ast_frame, wrap=tk.NONE, bg="#2b2b2b", fg="#a9b7c6", font=("Consolas", 10))
ast_display.pack(fill=tk.BOTH, expand=True)
table_pane.add(ast_frame)

main_pane.add(mid_frame)

# --- BOTTOM SECTION: Errors ---
bottom_frame = tk.Frame(main_pane)
tk.Label(bottom_frame, text="Compiler Output / Errors:", font=('Arial', 10, 'bold')).pack(anchor="w", padx=10, pady=(10, 0))
error_display = tk.Text(bottom_frame, height=6, state='disabled', bg="#f0f0f0")
error_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

error_display.tag_config("error_tag", foreground="red")
error_display.tag_config("success_tag", foreground="green")

main_pane.add(bottom_frame)

root.mainloop()