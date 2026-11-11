---
title: "C Array and Pointer Anatomy: Memory Layout, Decay, and sizeof Internals"
date: 2026-11-11 17:00:00 +0800
categories:
  - system
tags: system c compiler memory-management low-latency assembly
excerpt: >
  A first-principles deep dive into C array internals: why an array variable occupies zero bytes of pointer storage in memory, how the compiler symbol table resolves sizeof at compile time, Dennis Ritchie's historical B-language trade-off that birthed array decay, and the assembly mechanics of pointer arithmetic.
---

One of the most persistent confusions in systems programming is the relationship between arrays and pointers in C. Introductory textbooks often introduce the dangerous shorthand: *"an array is just a pointer."*

Then, the programmer encounters this code:

```c
#include <stdio.h>

void inspect(int param[10]) {
    printf("sizeof(param) = %zu\n", sizeof(param)); // Prints 8
}

int main(void) {
    int arr[10];
    printf("sizeof(arr)   = %zu\n", sizeof(arr));   // Prints 40
    inspect(arr);
    return 0;
}
```

If `arr` is just a pointer, why does `sizeof(arr)` evaluate to $40\,\text{bytes}$ on a 64-bit machine, while `sizeof(param)` evaluates to $8\,\text{bytes}$?

And if `arr` is *not* a pointer, where in memory is the pointer stored when we pass `arr` to a function? 

To answer these questions, we must step outside of surface syntax and look at C the way the compiler does: through the **symbol table**, the **type system**, and the **hardware memory layout**.

---

## 1. Physical Memory Layout: What Actually Exists in RAM?

The fundamental revelation of C arrays is simple:

> **There is no pointer object named `arr` in memory.**

When you declare a pointer:
```c
int x = 42;
int *p = &x;
```
The compiler allocates **$8\,\text{bytes}$ of physical storage** for `p` (on the stack, in a register, or in the data segment). That storage contains a $64\text{-bit}$ hardware memory address pointing to `x`. Notice that `p` is **not** an integer; it is a **pointer (`int *`)**:

```text
POINTER IN MEMORY (64-bit architecture):
Byte Range        Variable      Size      Value Stored
────────────────  ────────      ────      ───────────────────────────────────
0x7ffe0008..000f  int *p        8 bytes   0x7ffe0000  (64-bit memory address)
0x7ffe0004..0007  [padding]     4 bytes   (Stack alignment padding)
0x7ffe0000..0003  int x         4 bytes   42          (32-bit integer value)
```

Now, examine an array declaration:
```c
int arr[4] = {10, 20, 30, 40};
```
Each element in `arr` is an `int` ($4\,\text{bytes}$). The compiler allocates **$16\,\text{bytes}$ of contiguous storage** ($4 \text{ elements} \times 4\,\text{bytes}$). It does **not** allocate an extra $8\text{-byte}$ pointer variable to store the starting address of `arr`:

```text
ARRAY IN MEMORY:
Byte Range        Element       Size      Value Stored
────────────────  ────────      ────      ───────────────────────────────────
0x7ffe000c..000f  arr[3]        4 bytes   40  (32-bit integer value)
0x7ffe0008..000b  arr[2]        4 bytes   30  (32-bit integer value)
0x7ffe0004..0007  arr[1]        4 bytes   20  (32-bit integer value)
0x7ffe0000..0003  arr[0]        4 bytes   10  (32-bit integer value)
```

There is no variable holding `0x7ffe0000`. The identifier `arr` is purely a **compile-time label** (a symbol) that the compiler associates with the stack address offset `-16(%rbp)`.

| Property | Pointer (`int *p`) | Array (`int arr[4]`) |
| :--- | :--- | :--- |
| **Physical Storage** | Allocates 8 bytes to hold an address | Allocates 16 bytes for 4 integers |
| **Storage for Pointer** | Yes (in memory or register) | **Zero bytes** |
| **Address Value** | Can be reassigned (`p = q; p++`) | **Immutable label** (`arr = q` is illegal) |
| **Value Category** | Modifiable lvalue | Non-modifiable lvalue |

---

## 2. The Compiler Symbol Table: How `sizeof` Knows the Size

Programmers coming from Python or Java often assume `sizeof` is a runtime function call that queries memory metadata or header prefixes.

In C, **`sizeof` is a compile-time operator**. It emits zero CPU instructions at runtime.

### The Abstract Syntax Tree (AST)

When GCC or Clang parses your C code, it builds an internal **Symbol Table** and **Abstract Syntax Tree (AST)**:

```text
Declaration: int arr[10];
      │
      ▼
Compiler Symbol Table Record:
┌──────────────────┬────────────────────────────────────────────┐
│ Symbol Name      │ "arr"                                      │
│ Base Type        │ int (4 bytes, align 4)                     │
│ Type Category    │ ConstantArrayType                          │
│ Element Count    │ 10                                         │
│ Total Size       │ 10 * sizeof(int) = 40 bytes                │
│ Storage Offset   │ -40(%rbp)                                  │
└──────────────────┴────────────────────────────────────────────┘
```

When the compiler encounters `sizeof(arr)`:
1. It looks up the symbol `"arr"` in its local scope symbol table.
2. It inspects the type: `ConstantArrayType(element_type=int, count=10)`.
3. It multiplies: $10 \times 4 = 40$.
4. It completely replaces the AST node `sizeof(arr)` with the integer literal constant `40`.

Look at the generated x86-64 assembly for `printf("%zu\n", sizeof(arr));`:

```nasm
movl    $40, %esi          ; The constant 40 is hardcoded directly!
leaq    .LC0(%rip), %rdi   ; "%zu\n"
call    printf
```

No array length was read from RAM. No loop counted elements. The constant `40` was baked into the binary at compile time.

### The Single Exception: Variable Length Arrays (VLAs)

Since C99, if an array size depends on a runtime expression (`int arr[n]`), the compiler cannot know the size at compile time:

```c
void test_vla(int n) {
    int arr[n];
    size_t s = sizeof(arr);
}
```

In this rare case alone, `sizeof` generates runtime machine instructions:
```nasm
movslq  %edi, %rax         ; Load n
shlq    $2, %rax           ; Multiply by 4 (sizeof(int)) via bit shift
movq    %rax, -24(%rbp)    ; Store computed size
```

---

## 3. Array Decay: Dennis Ritchie's Historical Trade-off

If an array is not a pointer, why does this compile without errors?

```c
int arr[5] = {1, 2, 3, 4, 5};
int *p = arr; // Implicit conversion!
```

This phenomenon is known as **Array-to-Pointer Decay**.

### The Historical Origin (From B to C)

In C's predecessor language **B** (designed by Ken Thompson on the PDP-7), when you declared:
```text
auto v[10];
```
The compiler *actually allocated an independent pointer variable* `v`, allocated a separate 10-word vector elsewhere, and initialized `v` to point to the vector's first word.

When Dennis Ritchie created **C** to port Unix to the PDP-11, memory was severely constrained ($64\,\text{KB}$ address space). Ritchie realized two major problems with B's model:
1. Storing an explicit pointer for every array wasted 2 bytes of precious RAM.
2. If an array was placed inside a `struct`, the struct had to store the pointer *plus* the data, making nested memory structures bloated and non-contiguous.

Ritchie eliminated the pointer variable entirely. In C, an array became a pure block of contiguous storage. But to preserve B's elegant subscripting syntax (`v[i]`), Ritchie established the **Decay Rule** (codified in ISO C17 §6.3.2.1p3):

> *"Except when it is the operand of the `sizeof` operator, the `_Alignof` operator, or the unary `&` operator, or is a string literal used to initialize an array, an expression that has type 'array of type' is converted to an expression with type 'pointer to type' that points to the initial element of the array object and is not an lvalue."*

### What Happens in Machine Code During Decay?

When `arr` decays into a pointer, the compiler generates a **`lea` (Load Effective Address)** instruction:

```c
int *p = arr;
```

Assembly (x86-64 GCC):
```nasm
leaq    -32(%rbp), %rax    ; Calculate the address of arr[0] on the stack
movq    %rax, -8(%rbp)     ; Store that address into pointer variable p
```

Notice: `leaq` computes the address arithmetic without reading memory. It takes the address where `arr` lives on the stack frame and hands it over as an rvalue pointer.

### Why Function Parameters Decay Silently

When you write a function signature like this:
```c
void process(int a[100]) { ... }
```
The C compiler silently **rewrites the parameter type in the AST**:

$$\texttt{int a[100]} \quad \xrightarrow{\text{AST Rewrite}} \quad \texttt{int *a}$$

```text
What you wrote:                    What the compiler compiles:
void process(int a[100])    ───►   void process(int *a)
void process(int a[])       ───►   void process(int *a)
void process(int *a)        ───►   void process(int *a)
```

The bracket notation `[100]` in a parameter list is purely documentation for the programmer. To the compiler's symbol table, `a` has type `PointerType(int)`. 

This is why `sizeof(a)` inside `process` evaluates to **8 bytes** (the size of a 64-bit pointer), not $400\,\text{bytes}$. The array dimension information was discarded at the function boundary.

---

## 4. The Address Identity Trap: `arr` vs. `&arr[0]` vs. `&arr`

Consider this puzzle:

```c
int arr[5] = {10, 20, 30, 40, 50};

printf("%p\n", (void *)arr);
printf("%p\n", (void *)&arr[0]);
printf("%p\n", (void *)&arr);
```

When executed, all three lines output the **exact same hexadecimal address** (e.g., `0x7ffd1000`).

Why do they output the same address if they are different concepts? And what is the difference between them?

### Same Numerical Address, Different Types

```text
Memory Address: 0x7ffd1000
                │
                ├─► arr        (decayed) ──► Type: int *         (Step size: 4 bytes)
                ├─► &arr[0]              ──► Type: int *         (Step size: 4 bytes)
                └─► &arr                 ──► Type: int (*)[5]    (Step size: 20 bytes!)
```

The address is numerically identical because the array starts at byte `0x7ffd1000`, the first element starts at byte `0x7ffd1000`, and the entire array entity starts at byte `0x7ffd1000`.

However, their **types in the compiler's type system are radically different**. We can prove this using pointer arithmetic:

```c
printf("arr + 1  = %p\n", (void *)(arr + 1));
printf("&arr + 1 = %p\n", (void *)(&arr + 1));
```

Output:
```text
arr      = 0x7ffd1000
arr + 1  = 0x7ffd1004   (+4 bytes: jumps 1 integer)
&arr + 1 = 0x7ffd1014   (+20 bytes: jumps the ENTIRE array of 5 integers!)
```

```text
POINTER ARITHMETIC LEAPS:

 0x7ffd1000     0x7ffd1004     0x7ffd1008     0x7ffd100c     0x7ffd1010     0x7ffd1014
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│    arr[0]    │    arr[1]    │    arr[2]    │    arr[3]    │    arr[4]    │ (End of arr)
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
▲              ▲                                                           ▲
│              │                                                           │
arr            arr + 1 (+4 bytes)                                          &arr + 1 (+20 bytes!)
```

* `arr + 1` scales by `sizeof(*arr) = sizeof(int) = 4`.
* `&arr + 1` scales by `sizeof(*(&arr)) = sizeof(int[5]) = 20`.

---

## 5. Pointer Arithmetic Secrets Behind `a[i]` and `i[a]`

In C, the array subscript operator `[]` does not exist as a primitive memory access in machine code. It is defined by ISO C as pure syntactic sugar for pointer addition:

$$a[i] \equiv *(\,(a) + (i)\,)$$

Because addition is commutative:

$$a[i] \equiv *(\,(a) + (i)\,) \equiv *(\,(i) + (a)\,) \equiv i[a]$$

This means the following C code is **100% valid and compiles identically**:

```c
int arr[5] = {10, 20, 30, 40, 50};

int val1 = arr[3]; // Standard syntax
int val2 = 3[arr]; // Fully valid C! Both evaluate to 40.
```

### Hardware Mapping: x86-64 SIB Addressing

Modern x86-64 CPUs have direct hardware support for this exact arithmetic via the **Scale-Index-Base (SIB)** byte in machine instructions:

```text
Effective Address = Base Register + (Index Register * Scale) + Displacement
```

When you write `arr[i]`, where `arr` is at `-32(%rbp)` and `i` is in `%rcx`:

```nasm
movl    -32(%rbp, %rcx, 4), %eax
```

* **Base:** `%rbp` (stack frame pointer)
* **Displacement:** `-32` (offset of `arr[0]`)
* **Index:** `%rcx` (the variable `i`)
* **Scale:** `4` (hardware scales automatically by `sizeof(int)`)

The CPU calculates `Base + Displacement + (i * 4)` in a **single clock cycle**.

---

## 6. Multidimensional Arrays vs. Array of Pointers (`int[3][4]` vs. `int**`)

A frequent source of catastrophic cache misses in numerical computing and high-frequency trading is confusing a 2D array with a double pointer.

### True 2D Array: `int matrix[3][4]`
A 2D array is a **single, flat, contiguous memory allocation** of $3 \times 4 \times 4 = 48\,\text{bytes}$:

```text
STACK (Contiguous 48 Bytes):
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬───┐
│ [0][0]   │ [0][1]   │ [0][2]   │ [0][3]   │ [1][0]   │ [1][1]   │...│
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴───┘
0x00       0x04       0x08       0x0c       0x10       0x14
```

To access `matrix[row][col]`, the compiler emits single-cycle arithmetic:
$$\text{Address} = \text{base} + (\text{row} \times 4 + \text{col}) \times \text{sizeof(int)}$$

Zero pointer chasing. All rows sit contiguously in CPU L1/L2 cache lines.

### Array of Pointers: `int **ptr`
An array of pointers represents fragmented, scattered memory:

```text
Pointer Vector in RAM:
┌──────────────┐
│ ptr[0]       │ ──► Heap Chunk 0: [ 10 | 20 | 30 | 40 ] (Random L1 miss)
├──────────────┤
│ ptr[1]       │ ──► Heap Chunk 1: [ 50 | 60 | 70 | 80 ] (DRAM line miss)
├──────────────┤
│ ptr[2]       │ ──► Heap Chunk 2: [ 90 | 11 | 12 | 13 ]
└──────────────┘
```

Accessing `ptr[row][col]` requires **two serialized memory dereferences**:
1. Read `ptr[row]` from memory to obtain the row pointer address (Latency: ~4–80 ns on cache miss).
2. Read the integer at `*(row_ptr + col)` from memory.

| Metric | Flat 2D Array (`int[3][4]`) | Pointer to Pointers (`int**`) |
| :--- | :--- | :--- |
| **Allocations** | **1 contiguous allocation** | $N + 1$ fragmented allocations |
| **Pointer Overhead** | **0 bytes** | $3 \times 8 = 24\,\text{bytes}$ of pointers |
| **Dereferences to Read** | **0 pointer dereferences** (pure arithmetic) | **2 serialized memory lookups** |
| **Cache Locality** | **Optimal** (streaming hardware prefetch) | **Poor** (pointer chasing across heap) |

---

## 7. Summary Mental Model

To master C arrays, anchor your mental model to these five core principles:

1. **Arrays are Allocations, Not Pointers:** `int arr[10]` allocates 40 bytes for elements. It allocates zero bytes for an address pointer.
2. **`sizeof` is a Compiler Lookup:** `sizeof` queries the AST type symbol table at compile time, resolving to a hardcoded constant integer in the final machine code (with the sole exception of runtime VLAs).
3. **Decay is an Implicit Address Extraction:** In expressions, an array identifier automatically decays to a temporary rvalue pointer (`&arr[0]`) representing the start of its storage.
4. **Three Exceptions to Decay:** An array does **not** decay when it is the operand of `sizeof`, `_Alignof`, or unary `&`.
5. **Parameters are Always Pointers:** In function parameter declarations, `int arr[]` and `int arr[N]` are syntactic sugar for `int *arr`.
